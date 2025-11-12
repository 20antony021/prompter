"""
Schema Validator Service

Validates and generates JSON-LD structured data for knowledge pages.
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


class SchemaValidator:
    """Validates and generates JSON-LD structured data for SEO."""
    
    def __init__(self):
        """Initialize the schema validator."""
        pass
    
    def generate_article_schema(
        self,
        title: str,
        description: str,
        url: str,
        published_at: datetime,
        updated_at: Optional[datetime] = None,
        author: Optional[str] = None,
        organization: Optional[str] = None,
        image_url: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate Article schema (JSON-LD) for a knowledge page.
        
        Args:
            title: Article title
            description: Article description
            url: Canonical URL
            published_at: Publication date
            updated_at: Last updated date
            author: Author name
            organization: Organization name
            image_url: Featured image URL
            keywords: List of keywords
            
        Returns:
            JSON-LD schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "datePublished": published_at.isoformat(),
            "dateModified": (updated_at or published_at).isoformat(),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            }
        }
        
        # Add author
        if author:
            schema["author"] = {
                "@type": "Person",
                "name": author
            }
        
        # Add publisher/organization
        if organization:
            schema["publisher"] = {
                "@type": "Organization",
                "name": organization,
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://prompter.site/logo.png"
                }
            }
        
        # Add image
        if image_url:
            schema["image"] = {
                "@type": "ImageObject",
                "url": image_url
            }
        
        # Add keywords
        if keywords:
            schema["keywords"] = ", ".join(keywords)
        
        return schema
    
    def generate_organization_schema(
        self,
        name: str,
        url: str,
        description: Optional[str] = None,
        logo_url: Optional[str] = None,
        social_profiles: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate Organization schema (JSON-LD).
        
        Args:
            name: Organization name
            url: Organization website
            description: Organization description
            logo_url: Logo URL
            social_profiles: List of social media profile URLs
            
        Returns:
            JSON-LD schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": name,
            "url": url
        }
        
        if description:
            schema["description"] = description
        
        if logo_url:
            schema["logo"] = {
                "@type": "ImageObject",
                "url": logo_url
            }
        
        if social_profiles:
            schema["sameAs"] = social_profiles
        
        return schema
    
    def generate_faq_schema(
        self,
        questions_and_answers: List[Dict[str, str]]
    ) -> Dict:
        """
        Generate FAQ schema (JSON-LD).
        
        Args:
            questions_and_answers: List of {"question": "...", "answer": "..."} dicts
            
        Returns:
            JSON-LD schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for qa in questions_and_answers:
            schema["mainEntity"].append({
                "@type": "Question",
                "name": qa["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa["answer"]
                }
            })
        
        return schema
    
    def generate_breadcrumb_schema(
        self,
        breadcrumbs: List[Dict[str, str]]
    ) -> Dict:
        """
        Generate BreadcrumbList schema (JSON-LD).
        
        Args:
            breadcrumbs: List of {"name": "...", "url": "..."} dicts in order
            
        Returns:
            JSON-LD schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": []
        }
        
        for i, crumb in enumerate(breadcrumbs):
            schema["itemListElement"].append({
                "@type": "ListItem",
                "position": i + 1,
                "name": crumb["name"],
                "item": crumb["url"]
            })
        
        return schema
    
    def generate_product_schema(
        self,
        name: str,
        description: str,
        image_url: str,
        brand: str,
        rating: Optional[float] = None,
        review_count: Optional[int] = None,
        price: Optional[str] = None,
        currency: str = "USD"
    ) -> Dict:
        """
        Generate Product schema (JSON-LD).
        
        Args:
            name: Product name
            description: Product description
            image_url: Product image URL
            brand: Brand name
            rating: Average rating (1-5)
            review_count: Number of reviews
            price: Price as string
            currency: Currency code (ISO 4217)
            
        Returns:
            JSON-LD schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": name,
            "description": description,
            "image": image_url,
            "brand": {
                "@type": "Brand",
                "name": brand
            }
        }
        
        # Add aggregate rating
        if rating is not None and review_count is not None:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": rating,
                "reviewCount": review_count
            }
        
        # Add offers
        if price is not None:
            schema["offers"] = {
                "@type": "Offer",
                "price": price,
                "priceCurrency": currency,
                "availability": "https://schema.org/InStock"
            }
        
        return schema
    
    def validate_schema(self, schema: Dict) -> Dict:
        """
        Validate a JSON-LD schema.
        
        Args:
            schema: JSON-LD schema dictionary
            
        Returns:
            Validation result:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []
        
        # Check required fields
        if "@context" not in schema:
            errors.append("Missing @context field")
        
        if "@type" not in schema:
            errors.append("Missing @type field")
        
        # Type-specific validation
        schema_type = schema.get("@type")
        
        if schema_type == "Article":
            required = ["headline", "datePublished"]
            for field in required:
                if field not in schema:
                    errors.append(f"Missing required field for Article: {field}")
            
            # Warnings
            if "author" not in schema:
                warnings.append("Consider adding author information")
            if "image" not in schema:
                warnings.append("Consider adding an image for better SEO")
        
        elif schema_type == "Organization":
            required = ["name", "url"]
            for field in required:
                if field not in schema:
                    errors.append(f"Missing required field for Organization: {field}")
        
        elif schema_type == "Product":
            required = ["name", "image"]
            for field in required:
                if field not in schema:
                    errors.append(f"Missing required field for Product: {field}")
        
        # Check if schema is valid JSON
        try:
            json.dumps(schema)
        except (TypeError, ValueError) as e:
            errors.append(f"Schema is not valid JSON: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def combine_schemas(self, schemas: List[Dict]) -> Dict:
        """
        Combine multiple schemas into a single JSON-LD graph.
        
        Args:
            schemas: List of schema dictionaries
            
        Returns:
            Combined schema with @graph
        """
        if len(schemas) == 1:
            return schemas[0]
        
        return {
            "@context": "https://schema.org",
            "@graph": schemas
        }

