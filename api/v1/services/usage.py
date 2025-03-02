from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import datetime

from api.v1.models.usage_store import UsageStore, ToolAccess
class UsageStoreService:
    
    def create_tool_access(db: Session, usage_store_id: int, tool_name: str, access_count: int) -> ToolAccess:
        """
        Creates a new ToolAccess record in the database.

        :param db: SQLAlchemy session
        :param usage_store_id: The ID of the related UsageStore
        :param tool_name: The name of the tool
        :param access_count: The access count for the tool
        :return: The created ToolAccess record
        """
        new_tool_access = ToolAccess(
            tool_name=tool_name,
            access_count=access_count
        )
        
        try:
            db.add(new_tool_access)
            db.commit()
            db.refresh(new_tool_access)
            return new_tool_access
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        except Exception as e:
            db.rollback()
            print(f"An error occurred: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    def fetch_by_user(self, db: Session, ip_address: str) -> UsageStore | None:     
        print(ip_address)
        usage = db.query(UsageStore).filter_by(ip_address=ip_address).first()
        if not usage:
            return False
        return usage    
    
    def fetch_by_id(self, db: Session, id: int):
        print(id)
        usage = db.query(UsageStore).filter(UsageStore.id == id).one()
        if not usage:
            raise False
        return usage

    def update_tool_usage(self, db: Session, id: int, tool_name: str, value: int):
        tools_usage = self.fetch_by_id(db, id)
        if tools_usage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND ,detail="Tool Usage record not found")

        # Update the dictionary
        tool: ToolAccess  = next((tool for tool in tools_usage.tools if tool.tool_name == tool_name), None)
        tool.access_count = value        
        db.commit()
        return tool

    def get_tool_value(self, db: Session, id: int, tool_name: str):
        """
        Retrieve the value of a specific tool from the tools_accessed dictionary.

        :param db: SQLAlchemy session
        :param id: ID of the ToolsUsage record
        :param tool_name: Name of the tool to retrieve the value for
        :return: Value of the tool if found, otherwise None
        """
        tools_usage = self.get_tools_usage_by_id(db, id)
        if tools_usage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND ,detail="Tool Usage record not found")

        # Retrieve the tool value from the dictionary
        tool: ToolAccess  = next((tool for tool in tools_usage.tools if tool.tool_name == tool_name), None)
        return tool.access_count
    
    def get_or_create_tool_value(self, db: Session, id: int, tool_name: str):
        """
        Retrieve the value of a specific tool from the tools_accessed dictionary.
        If the tool does not exist, it creates it with a value of 0 and returns that value.

        :param db: SQLAlchemy session
        :param id: ID of the ToolsUsage record
        :param tool_name: Name of the tool to retrieve the value for
        :return: Value of the tool
        """
        tools_usage = self.get_tools_usage_by_id(db, id)
        if tools_usage is None:
            raise ValueError("ToolsUsage record not found")

        # Retrieve the dictionary
        tool: ToolAccess  = [tool.tool_name for tool in tools_usage.tools]

        # Check if the tool exists in the dictionary
        if tool_name in tool:
            value = tool.access_count
        else:
            # Tool does not exist, create it with a default value of 0
            new_tool = self.create_tool_access(
                db,
                id,
                tool_name,
                0
            )
            value = new_tool.access_count

        return value

    def create_usage_store_and_assign_tool(self, db: Session, ip_address: str, tool_name: str, access_count: int, tool_access_count: int) -> UsageStore:
        """
        Create a new UsageStore record and assign a ToolAccess to it.

        :param db: SQLAlchemy session
        :param tool_name: The name of the tool to assign
        :param access_count: The initial access count for the tool
        :return: The created UsageStore record
        """
        # Create a new UsageStore instance
        new_usage_store =  UsageStore(
            ip_address=ip_address,
            tool_access_count=access_count,
        )
        
        # Add the UsageStore record to the session
        db.add(new_usage_store)
        db.commit()  # Commit to generate the ID for the UsageStore
        
        # Create a new ToolAccess instance
        new_tool_access = ToolAccess(
            usage_store_id=new_usage_store.id,
            tool_name=tool_name,
            access_count=tool_access_count
        )
        
        # Add the ToolAccess record to the session
        db.add(new_tool_access)
        db.commit()  # Commit the ToolAccess record
        
        return new_usage_store
    
    
    def update_store_access_count(self, db: Session, id: str, value: int):
        store = self.fetch_by_user(db, id)
        store.tool_access_count = value
        db.commit()
        return store.tool_access_count
    
    def fetch_tool_access_by_usage_store_and_name(self, db: Session, usage_store_id: str, tool_name: str):
        """Find ToolAccess entries by usage_store_id and tool_name."""
        tool_access = db.query(ToolAccess).filter_by(
            usage_store_id=usage_store_id,
            tool_name=tool_name
        ).first()

        if not tool_access:
            raise HTTPException(status_code=404, detail=f'Tool access with {tool_name} not found')

        return tool_access


    def add_tool_count_by_id(self, db: Session, id:str, tool_name: str, value:int):
        usage = self.fetch_by_id(db, id)
        tool = self.fetch_tool_access_by_usage_store_and_name(db, id, tool_name)
        
        tool.access_count += value
        usage.last_accessed = datetime.utcnow()
        db.commit()
        tool.last_accessed = datetime.utcnow()
        db.commit()
        return tool.access_count
    
    def add_tool_access_count_by_user(self, db: Session, ip_address: str, value: int) -> int:
        """
        Increments the access count for a specific tool in the UsageStore record identified by the user ID.

        :param db: SQLAlchemy session object for database operations.
        :param ip_address: The visitors ip address of the UsageStore record to update.
        :param value: The increment value for the tool's access count.

        :return: The updated access count for the tool.
        """
        tool = self.fetch_by_user(db, ip_address)
        tool.tool_access_count += value
        db.commit()
        return tool.tool_access_count

usage_store_service = UsageStoreService()