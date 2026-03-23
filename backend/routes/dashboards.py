"""Dashboard CRUD API."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..models.base import get_session
from ..models.dashboard import Dashboard, DashboardTile
from ..models.user import User

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


class TileCreate(BaseModel):
    tile_type: str
    title: str | None = None
    config_json: str = "{}"
    grid_x: int = 0
    grid_y: int = 0
    grid_w: int = 4
    grid_h: int = 3


class TileResponse(BaseModel):
    id: str
    tile_type: str
    title: str | None
    config_json: str
    grid_x: int
    grid_y: int
    grid_w: int
    grid_h: int


class DashboardCreate(BaseModel):
    title: str
    description: str | None = None


class DashboardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class DashboardResponse(BaseModel):
    id: str
    title: str
    description: str | None
    tiles: list[TileResponse]
    created_at: str


def _to_response(d: Dashboard) -> DashboardResponse:
    return DashboardResponse(
        id=d.id,
        title=d.title,
        description=d.description,
        tiles=[
            TileResponse(
                id=t.id, tile_type=t.tile_type, title=t.title,
                config_json=t.config_json, grid_x=t.grid_x, grid_y=t.grid_y,
                grid_w=t.grid_w, grid_h=t.grid_h,
            )
            for t in sorted(d.tiles, key=lambda t: t.sort_order)
        ],
        created_at=d.created_at.isoformat(),
    )


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    body: DashboardCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dash = Dashboard(user_id=user.id, title=body.title, description=body.description)
    session.add(dash)
    session.commit()
    session.refresh(dash)
    return _to_response(dash)


@router.get("", response_model=list[DashboardResponse])
def list_dashboards(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    results = session.execute(
        select(Dashboard).where(Dashboard.user_id == user.id).order_by(Dashboard.updated_at.desc())
    ).scalars().all()
    return [_to_response(d) for d in results]


@router.get("/{dash_id}", response_model=DashboardResponse)
def get_dashboard(
    dash_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dash = session.get(Dashboard, dash_id)
    if dash is None or dash.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return _to_response(dash)


@router.put("/{dash_id}", response_model=DashboardResponse)
def update_dashboard(
    dash_id: str,
    body: DashboardUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dash = session.get(Dashboard, dash_id)
    if dash is None or dash.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    if body.title is not None:
        dash.title = body.title
    if body.description is not None:
        dash.description = body.description
    session.commit()
    session.refresh(dash)
    return _to_response(dash)


@router.delete("/{dash_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(
    dash_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dash = session.get(Dashboard, dash_id)
    if dash is None or dash.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    session.delete(dash)
    session.commit()


@router.post("/{dash_id}/tiles", response_model=TileResponse, status_code=status.HTTP_201_CREATED)
def add_tile(
    dash_id: str,
    body: TileCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dash = session.get(Dashboard, dash_id)
    if dash is None or dash.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    tile = DashboardTile(
        dashboard_id=dash_id,
        tile_type=body.tile_type,
        title=body.title,
        config_json=body.config_json,
        grid_x=body.grid_x,
        grid_y=body.grid_y,
        grid_w=body.grid_w,
        grid_h=body.grid_h,
        sort_order=len(dash.tiles),
    )
    session.add(tile)
    session.commit()
    session.refresh(tile)
    return TileResponse(
        id=tile.id, tile_type=tile.tile_type, title=tile.title,
        config_json=tile.config_json, grid_x=tile.grid_x, grid_y=tile.grid_y,
        grid_w=tile.grid_w, grid_h=tile.grid_h,
    )


@router.delete("/{dash_id}/tiles/{tile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tile(
    dash_id: str,
    tile_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    dash = session.get(Dashboard, dash_id)
    if dash is None or dash.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    tile = session.get(DashboardTile, tile_id)
    if tile is None or tile.dashboard_id != dash_id:
        raise HTTPException(status_code=404, detail="Tile not found")
    session.delete(tile)
    session.commit()
