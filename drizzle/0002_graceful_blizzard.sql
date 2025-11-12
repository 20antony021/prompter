CREATE TYPE "public"."mention_type" AS ENUM('direct', 'indirect', 'competitive');--> statement-breakpoint
CREATE TYPE "public"."sentiment" AS ENUM('positive', 'negative', 'neutral');--> statement-breakpoint
CREATE TABLE "mentions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"prompt_id" uuid NOT NULL,
	"topic_id" uuid NOT NULL,
	"model_result_id" uuid NOT NULL,
	"model" "model" NOT NULL,
	"mention_type" "mention_type" NOT NULL,
	"position" numeric,
	"context" text NOT NULL,
	"sentiment" "sentiment" NOT NULL,
	"confidence" numeric(3, 2),
	"extracted_text" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "mentions" ADD CONSTRAINT "mentions_prompt_id_prompts_id_fk" FOREIGN KEY ("prompt_id") REFERENCES "public"."prompts"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "mentions" ADD CONSTRAINT "mentions_topic_id_topics_id_fk" FOREIGN KEY ("topic_id") REFERENCES "public"."topics"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "mentions" ADD CONSTRAINT "mentions_model_result_id_prompt_results_id_fk" FOREIGN KEY ("model_result_id") REFERENCES "public"."prompt_results"("id") ON DELETE cascade ON UPDATE no action;