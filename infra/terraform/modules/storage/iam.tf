variable "github_actions_role_name" {
  type    = string
  default = ""
}

resource "aws_iam_role_policy" "github_s3_access" {
  count = var.github_actions_role_name != "" ? 1 : 0
  name  = "mlops-s3-artifacts"
  role  = var.github_actions_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
      Resource = [
        aws_s3_bucket.artifacts.arn,
        "${aws_s3_bucket.artifacts.arn}/*"
      ]
    }]
  })
}
