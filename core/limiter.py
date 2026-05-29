from fastapi import Depends
from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter

signup_limiter = RateLimiter(
    limiter=Limiter(Rate(5, Duration.MINUTE))
)

auth_limiter = RateLimiter(
    limiter=Limiter(Rate(5, Duration.MINUTE))
)

sensitive_txn_limiter = RateLimiter(
    limiter=Limiter(Rate(10, Duration.MINUTE))
)

deposit_limiter = RateLimiter(
    limiter=Limiter(Rate(30, Duration.MINUTE))
)