"""
Notes API Endpoints - Full CRUD with Version Control
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import Annotated, Optional
import uuid

from app.db.session import get_db
from app.models.entities import Note, Notebook, NoteVersion
from app.api.v1.endpoints.auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter()


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: list[str] = []
    notebook_id: Optional[str] = None
    is_public: bool = False


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None
    notebook_id: Optional[str] = None
    is_public: Optional[bool] = None


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    excerpt: Optional[str] = None
    tags: list[str]
    notebook_id: Optional[str]
    author_id: str
    is_public: bool
    view_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=dict)
async def list_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    notebook_id: Optional[str] = None,
):
    """List notes with pagination and filtering"""
    offset = (page - 1) * limit
    
    # Build query
    query = select(Note).where(Note.author_id == current_user["sub"])
    
    # Apply filters
    if search:
        query = query.where(Note.title.ilike(f"%{search}%") | Note.content.ilike(f"%{search}%"))
    
    if tag:
        query = query.where(func.json_array_length(Note.tags) > 0)  # Simplified tag filter
    
    if notebook_id:
        query = query.where(Note.notebook_id == notebook_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(Note.updated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    notes = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(note.id),
                "title": note.title,
                "excerpt": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                "tags": note.tags,
                "notebook_id": str(note.notebook_id) if note.notebook_id else None,
                "is_public": note.is_public,
                "view_count": note.view_count,
                "updated_at": note.updated_at.isoformat(),
            }
            for note in notes
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Create a new note"""
    # Validate notebook if provided
    if note_data.notebook_id:
        notebook_uuid = uuid.UUID(note_data.notebook_id)
        result = await db.execute(
            select(Notebook).where(
                and_(
                    Notebook.id == notebook_uuid,
                    Notebook.author_id == current_user["sub"]
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found"
            )
        notebook_uuid = notebook_uuid
    else:
        notebook_uuid = None
    
    # Create note
    note = Note(
        title=note_data.title,
        content=note_data.content,
        tags=note_data.tags,
        notebook_id=notebook_uuid,
        author_id=current_user["sub"],
        is_public=note_data.is_public,
    )
    
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    # Create initial version
    version = NoteVersion(
        note_id=note.id,
        title=note.title,
        content=note.content,
        version_number=1,
        author_id=current_user["sub"],
    )
    db.add(version)
    await db.commit()
    
    return NoteResponse.model_validate(note)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get a specific note"""
    note_uuid = uuid.UUID(note_id)
    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_uuid,
                Note.author_id == current_user["sub"]
            )
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Increment view count
    note.view_count += 1
    await db.commit()
    
    return NoteResponse.model_validate(note)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update a note"""
    note_uuid = uuid.UUID(note_id)
    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_uuid,
                Note.author_id == current_user["sub"]
            )
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Update fields
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    
    note.updated_at = datetime.utcnow()
    
    # Create new version if content changed
    if note_data.content:
        # Get max version number
        version_result = await db.execute(
            select(func.max(NoteVersion.version_number)).where(
                NoteVersion.note_id == note.id
            )
        )
        max_version = version_result.scalar() or 0
        
        version = NoteVersion(
            note_id=note.id,
            title=note.title,
            content=note.content,
            version_number=max_version + 1,
            author_id=current_user["sub"],
        )
        db.add(version)
    
    await db.commit()
    await db.refresh(note)
    
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Delete a note"""
    note_uuid = uuid.UUID(note_id)
    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_uuid,
                Note.author_id == current_user["sub"]
            )
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    await db.delete(note)
    await db.commit()


@router.get("/{note_id}/versions", response_model=list)
async def get_note_versions(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get all versions of a note"""
    note_uuid = uuid.UUID(note_id)
    
    # Verify note ownership
    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_uuid,
                Note.author_id == current_user["sub"]
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Get versions
    versions_result = await db.execute(
        select(NoteVersion)
        .where(NoteVersion.note_id == note_uuid)
        .order_by(NoteVersion.version_number.desc())
    )
    versions = versions_result.scalars().all()
    
    return [
        {
            "version_number": v.version_number,
            "title": v.title,
            "content": v.content,
            "created_at": v.created_at.isoformat(),
            "author_id": str(v.author_id),
        }
        for v in versions
    ]
