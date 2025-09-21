# backend/app/api/v1/endpoints/menu.py

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient

from app.db.mongodb import get_database
from app.schemas.category import Category, CategoryCreate
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.schemas.menu_item import MenuItem, MenuItemCreate

router = APIRouter()

@router.post(
    "/categories/",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    tags=["Menu Categories"]
)
async def create_category(
    category: CategoryCreate,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Create a new menu category.
    """
    category_dict = category.model_dump()

    # Insert the new category into the 'categories' collection
    result = await db["categories"].insert_one(category_dict)

    # Retrieve the newly created document to return it in the response
    created_category = await db["categories"].find_one({"_id": result.inserted_id})

    if created_category is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create the category."
        )

    return created_category

@router.get(
    "/categories/{category_id}",
    response_model=Category,
    tags=["Menu Categories"]
)
async def get_category(
    category_id: str,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Retrieve a single menu category by its ID.
    """
    # We must convert the string ID from the path to a MongoDB ObjectId
    try:
        category_oid = ObjectId(category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for category_id: {category_id}"
        )
        
    category = await db["categories"].find_one({"_id": category_oid})
    
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
        
    return Category.model_validate(category)


@router.get(
    "/categories/",
    response_model=List[Category],
    tags=["Menu Categories"]
)
async def list_categories(
    name: str | None = None, # <-- ADD THE OPTIONAL NAME PARAMETER HERE
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Retrieve a list of menu categories.
    Optionally, filter by category name (case-insensitive).
    """
    query = {}
    if name:
        # Use a case-insensitive regex for a more user-friendly search
        query["name"] = {"$regex": f"^{name}$", "$options": "i"}

    categories_cursor = db["categories"].find(query)
    categories_list = await categories_cursor.to_list(length=100)

    return [Category.model_validate(category) for category in categories_list]

@router.put(
    "/categories/{category_id}",
    response_model=Category,
    tags=["Menu Categories"]
)
async def update_category(
    category_id: str,
    category_update: CategoryCreate, # We can reuse the Create schema for the update data
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Update an existing menu category.
    """
    try:
        category_oid = ObjectId(category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for category_id: {category_id}"
        )

    # Convert the Pydantic model to a dictionary for MongoDB's $set operator
    update_data = category_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    # Perform the update
    result = await db["categories"].update_one(
        {"_id": category_oid},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Retrieve and return the updated document
    updated_category = await db["categories"].find_one({"_id": category_oid})
    return Category.model_validate(updated_category)

@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Menu Categories"]
)
async def delete_category(
    category_id: str,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Delete a menu category by its ID.
    """
    try:
        category_oid = ObjectId(category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for category_id: {category_id}"
        )

    # Perform the delete operation
    result = await db["categories"].delete_one({"_id": category_oid})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    # A 204 response should not have a body
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/items/",
    response_model=MenuItem,
    status_code=status.HTTP_201_CREATED,
    tags=["Menu Items"]
)
async def create_menu_item(
    item: MenuItemCreate,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Create a new menu item.
    """
    # --- Validation Step ---
    # Check if the category_id exists before creating the item
    try:
        category_oid = ObjectId(item.category_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for category_id: {item.category_id}"
        )

    category = await db["categories"].find_one({"_id": category_oid})
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {item.category_id} not found."
        )
    
    # --- Creation Step ---
    item_dict = item.model_dump()
    result = await db["menu_items"].insert_one(item_dict)
    created_item = await db["menu_items"].find_one({"_id": result.inserted_id})
    
    if not created_item:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create the menu item."
        )

    return MenuItem.model_validate(created_item)


@router.get(
    "/items/",
    response_model=List[MenuItem],
    tags=["Menu Items"]
)
async def list_menu_items(
    category_id: str | None = None, # Optional query parameter to filter
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Retrieve a list of menu items.
    Optionally, filter by category_id.
    """
    query = {}
    if category_id:
        try:
            # Add the category filter to our query
            query["category_id"] = str(ObjectId(category_id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ObjectId format for category_id: {category_id}"
            )
            
    items_cursor = db["menu_items"].find(query)
    items_list = await items_cursor.to_list(length=1000) # Increased length for full menu
    
    return [MenuItem.model_validate(item) for item in items_list]


@router.get(
    "/items/{item_id}",
    response_model=MenuItem,
    tags=["Menu Items"]
)
async def get_menu_item(
    item_id: str,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Retrieve a single menu item by its ID.
    """
    try:
        item_oid = ObjectId(item_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for item_id: {item_id}"
        )
        
    item = await db["menu_items"].find_one({"_id": item_oid})
    
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with id {item_id} not found"
        )
        
    return MenuItem.model_validate(item)


@router.put(
    "/items/{item_id}",
    response_model=MenuItem,
    tags=["Menu Items"]
)
async def update_menu_item(
    item_id: str,
    item_update: MenuItemCreate,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Update an existing menu item.
    """
    try:
        item_oid = ObjectId(item_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for item_id: {item_id}"
        )

    # --- Validation Step ---
    # If the category is being changed, ensure the new category exists
    if item_update.category_id:
        try:
            category_oid = ObjectId(item_update.category_id)
            category = await db["categories"].find_one({"_id": category_oid})
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {item_update.category_id} not found."
                )
        except Exception:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ObjectId format for category_id: {item_update.category_id}"
            )

    # --- Update Step ---
    update_data = item_update.model_dump(exclude_unset=True)
    result = await db["menu_items"].update_one(
        {"_id": item_oid},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with id {item_id} not found"
        )

    updated_item = await db["menu_items"].find_one({"_id": item_oid})
    return MenuItem.model_validate(updated_item)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Menu Items"]
)
async def delete_menu_item(
    item_id: str,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Delete a menu item by its ID.
    """
    try:
        item_oid = ObjectId(item_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ObjectId format for item_id: {item_id}"
        )

    result = await db["menu_items"].delete_one({"_id": item_oid})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with id {item_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
