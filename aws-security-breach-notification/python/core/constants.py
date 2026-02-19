"""Constants for AWS security monitoring."""

# Whitelisted ports that don't trigger alerts
INGRESS_WHITELIST_PORTS = [80, 443, 53]
EGRESS_WHITELIST_PORTS = [80, 443, 587]

# Public CIDR blocks
PUBLIC_IPV4_CIDR = "0.0.0.0/0"
PUBLIC_IPV6_CIDR = "::/0"
