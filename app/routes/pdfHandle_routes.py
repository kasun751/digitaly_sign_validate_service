from flask import Blueprint
from ..controllers import signDocument, documentVarify, documentUpload

pdfHandle_bp = Blueprint("sign_bp", __name__)


@pdfHandle_bp.route('/signPdf', methods=['post'])
def sign_pdf():
    return signDocument()


@pdfHandle_bp.route('/validatePdf', methods=['post'])
def validate_Pdf():
    return documentVarify()


@pdfHandle_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    return documentUpload()
