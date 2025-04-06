import os
from secrets import token_hex
from datetime import datetime, timedelta
from typing import List, Optional
import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.auth.auth import get_current_user
from src.db.models import User, Article, ArticleHistory, ArticleImage
from src.db.database import get_db
from src.core.config import settings
from src.article.schemas import ArticleResponse, ArticleHistoryResponse

router = APIRouter(prefix="/articles", tags=["articles"])

async def save_uploaded_file(file: UploadFile, directory: str) -> str:
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    filename = f"article_{token_hex(4)}{file_ext}"
    file_path = os.path.join(directory, filename)
    
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(await file.read())
    return filename

@router.get("/", response_model=List[ArticleResponse])
async def get_articles(
    title: Optional[str] = None,
    author_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = (
        select(Article)
        .where(Article.is_deleted == False)
        .offset(offset)
        .limit(limit)
    )
    
    if title:
        query = query.where(Article.title.ilike(f"%{title}%"))
    if author_id:
        query = query.where(Article.author_id == author_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    title: str = Form(..., min_length=3, max_length=255),
    content: str = Form(..., max_length=5000),
    images: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        article = Article(
            title=title,
            content=content,
            author_id=current_user.user_id
        )
        db.add(article)
        await db.flush()

        if images:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            for image in images:
                filename = await save_uploaded_file(image, settings.UPLOAD_DIR)
                article_image = ArticleImage(
                    article_id=article.id,
                    image_path=filename
                )
                db.add(article_image)

        history_entry = ArticleHistory(
            article_id=article.id,
            user_id=current_user.user_id,
            event="CREATE",
            new_title=title,
            new_content=content
        )
        db.add(history_entry)
        
        await db.commit()
        await db.refresh(article)
        return article

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании статьи: {str(e)}"
        )
    
@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    title: Optional[str] = Form(default=None, min_length=3, max_length=255),
    content: Optional[str] = Form(default=None, max_length=5000),
    images: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Article)
            .where(Article.id == article_id, Article.is_deleted == False)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Статья не найдена")
        
        if article.author_id != current_user.user_id and current_user.role_id != 2:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        changes_made = False
        old_title = article.title
        old_content = article.content

        if title is not None and title != article.title:
            article.title = title
            changes_made = True
        if content is not None and content != article.content:
            article.content = content
            changes_made = True

        if images:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            for image in images:
                filename = await save_uploaded_file(image, settings.UPLOAD_DIR)
                db.add(ArticleImage(
                    article_id=article.id,
                    image_path=filename
                ))
            changes_made = True

        if changes_made:
            history_entry = ArticleHistory(
                article_id=article.id,
                user_id=current_user.user_id,
                event="UPDATE",
                old_title=old_title if title is not None and title != old_title else None,
                new_title=title if title is not None and title != old_title else None,
                old_content=old_content if content is not None and content != old_content else None,
                new_content=content if content is not None and content != old_content else None
            )
            db.add(history_entry)

        await db.commit()
        await db.refresh(article)
        return article

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении статьи: {str(e)}"
        )

@router.delete("/{article_id}", response_model=dict)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Article)
            .where(Article.id == article_id, Article.is_deleted == False)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Статья не найдена")
        
        if article.author_id != current_user.user_id and current_user.role_id != 2:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        article.is_deleted = True
        article.deleted_at = datetime.utcnow()
        
        history_entry = ArticleHistory(
            article_id=article.id,
            user_id=current_user.user_id,
            event="DELETE",
            old_title=article.title,
            old_content=article.content
        )
        db.add(history_entry)
        
        await db.commit()
        return {"message": "Статья успешно удалена"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении статьи: {str(e)}"
        )

@router.post("/{article_id}/restore", response_model=ArticleResponse)
async def restore_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Article)
            .where(
                Article.id == article_id,
                Article.is_deleted == True,
                Article.deleted_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(
                status_code=404,
                detail="Статья не найдена или срок восстановления истек"
            )
        
        if article.author_id != current_user.user_id and current_user.role_id != 2:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        article.is_deleted = False
        article.deleted_at = None
        
        history_entry = ArticleHistory(
            article_id=article.id,
            user_id=current_user.user_id,
            event="RESTORE",
            new_title=article.title,
            new_content=article.content
        )
        db.add(history_entry)
        
        await db.commit()
        await db.refresh(article)
        return article

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при восстановлении статьи: {str(e)}"
        )

@router.get("/{article_id}/history", response_model=List[ArticleHistoryResponse])
async def get_article_history(
    article_id: int,
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Article)
            .where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Статья не найдена")
        
        if article.author_id != current_user.user_id and current_user.role_id != 2:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        result = await db.execute(
            select(ArticleHistory)
            .where(ArticleHistory.article_id == article_id)
            .order_by(ArticleHistory.changed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        return result.scalars().all()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении истории статьи: {str(e)}"
        )
