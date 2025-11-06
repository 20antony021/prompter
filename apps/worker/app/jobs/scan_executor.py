"""Scan execution job."""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List

# Add parent directory to path to import from api
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../api"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.llm_providers import get_provider
from app.models.brand import Brand
from app.models.mention import Mention
from app.models.prompt import PromptSet, PromptSetItem
from app.models.scan import ScanResult, ScanRun, ScanStatus
from app.services.mention_extractor import MentionExtractor

logger = logging.getLogger(__name__)

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


async def execute_scan_run_async(scan_run_id: int) -> None:
    """
    Execute a scan run asynchronously.

    Args:
        scan_run_id: ID of scan run to execute
    """
    db = SessionLocal()

    try:
        # Get scan run
        scan_run = db.query(ScanRun).filter(ScanRun.id == scan_run_id).first()

        if not scan_run:
            logger.error(f"Scan run {scan_run_id} not found")
            return

        # Update status
        scan_run.status = ScanStatus.RUNNING
        scan_run.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Executing scan run {scan_run_id}")

        # Get brand
        brand = db.query(Brand).filter(Brand.id == scan_run.brand_id).first()

        # Get prompt set
        prompt_set = (
            db.query(PromptSet).filter(PromptSet.id == scan_run.prompt_set_id).first()
        )

        # Get prompt set items
        prompt_items = (
            db.query(PromptSetItem)
            .filter(PromptSetItem.prompt_set_id == prompt_set.id)
            .all()
        )

        # Execute prompts for each model
        models = scan_run.model_matrix_json

        for model_key in models:
            logger.info(f"Running prompts with model: {model_key}")

            try:
                provider = get_provider(model_key)
            except Exception as e:
                logger.error(f"Failed to get provider for {model_key}: {e}")
                continue

            for prompt_item in prompt_items:
                try:
                    # Get prompt text
                    prompt_text = prompt_item.prompt_template.text

                    # Substitute variables
                    if prompt_item.variables_json:
                        for key, value in prompt_item.variables_json.items():
                            prompt_text = prompt_text.replace(f"{{{key}}}", value)

                    # Generate response
                    system_prompt = """You are a helpful AI assistant. Provide accurate, factual information.
Do not fabricate URLs or sources. If you don't know something, say so."""

                    response = await provider.generate(
                        prompt=prompt_text,
                        system_prompt=system_prompt,
                        temperature=0.3,
                        max_tokens=2000,
                    )

                    # Save result
                    scan_result = ScanResult(
                        scan_run_id=scan_run.id,
                        model_name=model_key,
                        prompt_text=prompt_text,
                        raw_response=response.text,
                        parsed_json=response.raw_response,
                    )

                    db.add(scan_result)
                    db.commit()
                    db.refresh(scan_result)

                    # Extract mentions
                    extractor = MentionExtractor(db, brand)
                    mentions = extractor.extract_mentions(response.text)

                    # Save mentions
                    for mention_data in mentions:
                        mention = Mention(
                            scan_result_id=scan_result.id,
                            entity_name=mention_data["entity_name"],
                            entity_type=mention_data["entity_type"],
                            sentiment=mention_data.get("sentiment"),
                            position_index=mention_data.get("position_index"),
                            confidence=mention_data.get("confidence"),
                            cited_urls_json=mention_data.get("cited_urls"),
                        )
                        db.add(mention)

                    db.commit()

                    logger.info(
                        f"Processed prompt for {model_key}, found {len(mentions)} mentions"
                    )

                except Exception as e:
                    logger.error(f"Error processing prompt with {model_key}: {e}")
                    continue

        # Update scan run status
        scan_run.status = ScanStatus.DONE
        scan_run.finished_at = datetime.utcnow()
        db.commit()

        logger.info(f"Scan run {scan_run_id} completed successfully")

    except Exception as e:
        logger.error(f"Error executing scan run {scan_run_id}: {e}")

        # Mark as failed
        try:
            scan_run = db.query(ScanRun).filter(ScanRun.id == scan_run_id).first()
            if scan_run:
                scan_run.status = ScanStatus.FAILED
                scan_run.finished_at = datetime.utcnow()
                db.commit()
        except:
            pass

    finally:
        db.close()


def execute_scan_run(scan_run_id: int) -> None:
    """
    Synchronous wrapper for async scan execution.

    Args:
        scan_run_id: ID of scan run to execute
    """
    asyncio.run(execute_scan_run_async(scan_run_id))

