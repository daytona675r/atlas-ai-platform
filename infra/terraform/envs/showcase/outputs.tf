output "bucket_name" {
  value = try(module.storage[0].bucket_name, null)
}

output "bucket_arn" {
  value = try(module.storage[0].bucket_arn, null)
}
