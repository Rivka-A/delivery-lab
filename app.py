
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

app = FastAPI()

deliveries = {}
next_id = 1

VALID_STATUSES = ["created", "in_transit", "delivered"]


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request"}
    )


class DeliveryCreate(BaseModel):
    recipient: str = Field(min_length=1)
    address: str = Field(min_length=1)


class StatusUpdate(BaseModel):
    status: str = Field(min_length=1)



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/deliveries", status_code=201)
def create_delivery(delivery: DeliveryCreate):
    global next_id

    recipient = delivery.recipient.strip()
    address = delivery.address.strip()

    if not recipient or not address:
        raise HTTPException(
            status_code=400,
            detail="Recipient and address cannot be empty"
        )

    new_delivery = {
        "id": next_id,
        "recipient": recipient,
        "address": address,
        "status": "created"
    }

    deliveries[next_id] = new_delivery
    next_id += 1

    return new_delivery

@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    return deliveries[delivery_id]



@app.get("/deliveries")
def list_deliveries(status: Optional[str] = None):
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    result = list(deliveries.values())

    if status is not None:
        result = [
            delivery
            for delivery in result
            if delivery["status"] == status
        ]

    return result



@app.patch("/deliveries/{delivery_id}/status")
def update_delivery_status(
    delivery_id: int,
    update: StatusUpdate
):
    if delivery_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    new_status = update.status

    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    current_status = deliveries[delivery_id]["status"]

    current_index = VALID_STATUSES.index(current_status)
    new_index = VALID_STATUSES.index(new_status)

    if new_index != current_index + 1:
        raise HTTPException(
            status_code=409,
            detail="Invalid status transition"
        )

    deliveries[delivery_id]["status"] = new_status

    return deliveries[delivery_id]




@app.delete("/deliveries/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    if deliveries[delivery_id]["status"] != "created":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a delivery that has already been processed"
        )

    del deliveries[delivery_id]

    return Response(status_code=204)






