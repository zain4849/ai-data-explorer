"""Dataset management routes: list, get schema, delete uploaded datasets."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..db import db_manager
from ..models.base import get_session
from ..models.dataset import Dataset
from ..models.user import User

router = APIRouter(prefix="/datasets", tags=["datasets"])



class DatasetResponse(BaseModel):
    id: str
    name: str
    table_name: str
    file_type: str
    row_count: int
    columns: list[str]
    created_at: str


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rows = session.execute(
        select(Dataset)
        .where(Dataset.user_id == user.id)
        .order_by(Dataset.created_at.desc())
    ).scalars().all()

    return [
        DatasetResponse(
            id=ds.id,
            name=ds.name,
            table_name=ds.table_name,
            file_type=ds.file_type,
            row_count=ds.row_count,
            columns=json.loads(ds.columns_json) if ds.columns_json else [],
            created_at=ds.created_at.isoformat() if ds.created_at else "",
        )
        for ds in rows
    ]


@router.get("/{dataset_id}/schema")
def dataset_schema(
    dataset_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    ds = session.get(Dataset, dataset_id)
    if ds is None or ds.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")

    connector = db_manager.get_connector(user.id)
    try:
        cols = connector.get_table_schema(ds.table_name)
        return [c.to_dict() for c in cols]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    ds = session.get(Dataset, dataset_id)
    if ds is None or ds.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Drop the table from user's DuckDB
    try:
        conn = db_manager.get_connection(user.id)
        conn.execute(f'DROP TABLE IF EXISTS "{ds.table_name}"')
    except Exception:
        pass

    # Remove the stored file
    try:
        p = Path(ds.file_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    session.delete(ds)
    session.commit()
