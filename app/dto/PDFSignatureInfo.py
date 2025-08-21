from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class PDFSignatureInfo:
    signer_email: Optional[str] = None
    signer_common_name: Optional[str] = None
    signer_organization: Optional[str] = None
    trust_anchor: Optional[str] = None
    is_trusted: bool = False
    is_signature_valid: bool = False
    signature_mechanism: Optional[str] = None
    signing_time: Optional[str] = None
    covers_entire_file: bool = False
    bottom_line: Optional[str] = None  # <-- NEW FIELD

    def to_dict(self):
        return asdict(self)
