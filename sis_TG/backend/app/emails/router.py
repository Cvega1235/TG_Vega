from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_role
from app.users.models import User
from app.emails.schemas import SendContactEmailRequest, SendContactEmailResponse
from app.emails.service import send_contact_email

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.post("/send-contact", response_model=SendContactEmailResponse)
def send_contact(
    data: SendContactEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    try:
        send_contact_email(
            db=db,
            restaurant_id=data.restaurant_id,
            to_email=data.to_email,
            subject=data.subject,
            body=data.body,
            sender_user_id=str(current_user.id),
            sender_name=current_user.full_name,
        )
        return SendContactEmailResponse(success=True, message="Email enviado correctamente")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar el email: {e}")
