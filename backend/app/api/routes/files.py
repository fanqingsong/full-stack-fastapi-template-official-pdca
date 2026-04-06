import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.minio import minio_client
from app.crud import delete_file, get_file_by_id, get_files_by_owner, get_files_count_by_owner
from app.models import File, FileCreate, FilePublic, FilesPublic, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/", response_model=FilesPublic)
def read_files(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve files.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(File)
        count = session.exec(count_statement).one()
        statement = (
            select(File).order_by(File.created_at.desc()).offset(skip).limit(limit)
        )
        files = session.exec(statement).all()
    else:
        count = get_files_count_by_owner(session=session, owner_id=current_user.id)
        files = get_files_by_owner(
            session=session, owner_id=current_user.id, skip=skip, limit=limit
        )

    return FilesPublic(data=files, count=count)


@router.get("/{id}", response_model=FilePublic)
def read_file(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get file metadata by ID.
    """
    file = get_file_by_id(session=session, file_id=id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and (file.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return file


@router.post("/upload", response_model=FilePublic)
async def upload_file(
    *, session: SessionDep, current_user: CurrentUser, file: UploadFile
) -> Any:
    """
    Upload a new file.
    """
    logger.info(f"[UPLOAD START] User: {current_user.id}, File object: {file}, Filename: {file.filename}")

    # Validate filename
    if not file or not file.filename:
        logger.error("[UPLOAD ERROR] File or filename is empty")
        raise HTTPException(status_code=422, detail="File name cannot be empty")

    # Read file content
    logger.info(f"[UPLOAD] Reading file content...")
    try:
        content = await file.read()
        file_size = len(content)
        content_type = file.content_type or "application/octet-stream"
        logger.info(f"[UPLOAD] File read successfully: size={file_size}, type={content_type}")
    except Exception as e:
        logger.error(f"[UPLOAD ERROR] Failed to read file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}") from e

    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{current_user.id}/{uuid.uuid4()}.{file_extension}"
    logger.info(f"[UPLOAD] Generated unique filename: {unique_filename}")

    # Upload to MinIO
    logger.info(f"[UPLOAD] Starting MinIO upload...")
    try:
        minio_client.upload_file(
            file_data=content,
            filename=unique_filename,
            content_type=content_type,
        )
        logger.info(f"[UPLOAD] MinIO upload successful")
    except RuntimeError as e:
        logger.error(f"[UPLOAD ERROR] MinIO upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"[UPLOAD ERROR] Unexpected error during MinIO upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"MinIO upload error: {e}") from e

    # Save file metadata to database
    logger.info(f"[UPLOAD] Saving metadata to database...")
    try:
        file_in = FileCreate(
            filename=unique_filename,
            original_filename=file.filename or "unnamed",
            content_type=content_type,
            file_size=file_size,
        )

        db_file = File.model_validate(file_in, update={"owner_id": current_user.id})
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
        logger.info(f"[UPLOAD SUCCESS] File saved to database: {db_file.id}")
    except Exception as e:
        logger.error(f"[UPLOAD ERROR] Database save failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e

    return db_file


@router.get("/{id}/download")
def download_file(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Download a file.
    """
    logger.info(f"[DOWNLOAD START] File ID: {id}, User: {current_user.id}")

    file = get_file_by_id(session=session, file_id=id)
    if not file:
        logger.error(f"[DOWNLOAD ERROR] File not found: {id}")
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and (file.owner_id != current_user.id):
        logger.error(f"[DOWNLOAD ERROR] Permission denied for user {current_user.id} on file {id}")
        raise HTTPException(status_code=403, detail="Not enough permissions")

    logger.info(f"[DOWNLOAD] Fetching from MinIO: {file.filename}")
    try:
        file_content = minio_client.get_file(file.filename)
        logger.info(f"[DOWNLOAD SUCCESS] File downloaded: {file.original_filename} ({len(file_content)} bytes)")
        return Response(
            content=file_content,
            media_type=file.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file.original_filename}"'
            },
        )
    except RuntimeError as e:
        logger.error(f"[DOWNLOAD ERROR] MinIO error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{id}/url")
def get_file_url(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID, expires_in: int = 3600
) -> Any:
    """
    Get a presigned URL for file download.
    """
    file = get_file_by_id(session=session, file_id=id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and (file.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        url = minio_client.get_file_url(file.filename, expires_in=expires_in)
        return {"url": url, "expires_in": expires_in}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{id}")
def delete_file_endpoint(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a file.
    """
    file = get_file_by_id(session=session, file_id=id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and (file.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Delete from MinIO
    try:
        minio_client.delete_file(file.filename)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    # Delete from database
    delete_file(session=session, db_file=file)

    return Message(message="File deleted successfully")
