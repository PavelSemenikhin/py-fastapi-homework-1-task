from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.database.models import MovieModel
from src.schemas.movies import (
    MovieDetailResponseSchema,
    MovieListResponseSchema
)

router = APIRouter()


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_detail_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = res.scalars().one_or_none()
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return db_movie


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page
    res = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.asc())
        .offset(offset)
        .limit(per_page)
    )
    movies = res.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    count_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = count_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/theater/movies/"
    prev_page = None if page == 1 else f"{base_url}?page={page - 1}&per_page={per_page}"
    next_page = None if page >= total_pages else f"{base_url}?page={page + 1}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )
