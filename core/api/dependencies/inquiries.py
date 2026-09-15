from fastapi import Request

from core.shopping.inquiries import InquiryRepository


def get_inquiry_repository(request: Request) -> InquiryRepository:
    repository = getattr(request.app.state, "inquiry_repository", None)
    if repository is None:
        raise RuntimeError("Inquiry repository is not composed")
    return repository
