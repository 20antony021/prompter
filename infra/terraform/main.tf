terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "prompter-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# S3 Bucket for Assets
resource "aws_s3_bucket" "assets" {
  bucket = "prompter-assets-${var.environment}"

  tags = {
    Name        = "Prompter Assets"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "assets_versioning" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://prompter.site", "https://*.prompter.site"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# IAM User for S3 Access
resource "aws_iam_user" "s3_access" {
  name = "prompter-s3-${var.environment}"
}

resource "aws_iam_access_key" "s3_access" {
  user = aws_iam_user.s3_access.name
}

resource "aws_iam_user_policy" "s3_access" {
  name = "s3-access"
  user = aws_iam_user.s3_access.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.assets.arn,
          "${aws_s3_bucket.assets.arn}/*"
        ]
      }
    ]
  })
}

# RDS PostgreSQL (Optional - can use Neon/Supabase instead)
resource "aws_db_subnet_group" "main" {
  name       = "prompter-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "Prompter DB Subnet Group"
    Environment = var.environment
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "prompter-${var.environment}"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_encrypted     = true

  db_name  = "prompter"
  username = "prompter"
  password = var.db_password

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "prompter-${var.environment}-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  performance_insights_enabled = true

  tags = {
    Name        = "Prompter Database"
    Environment = var.environment
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "prompter-rds-${var.environment}"
  description = "Security group for Prompter RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "Prompter RDS Security Group"
    Environment = var.environment
  }
}

# Outputs
output "s3_bucket_name" {
  value = aws_s3_bucket.assets.id
}

output "s3_access_key_id" {
  value     = aws_iam_access_key.s3_access.id
  sensitive = true
}

output "s3_secret_access_key" {
  value     = aws_iam_access_key.s3_access.secret
  sensitive = true
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "rds_connection_string" {
  value     = "postgresql://${aws_db_instance.postgres.username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive = true
}

