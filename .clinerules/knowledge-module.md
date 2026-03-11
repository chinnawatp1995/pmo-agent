## Knolwedge Module

## Repository Layer

### Persistence

#### LightRAG 
    ** Use context7 MCP to get LightRAG document before implement
    - Create LightRAG instance
    - Config .env file to persist in Postgresql and FalkoreDB  

#### Postgresql
    - interfaces used to support operations

## Application Layer

### Usecase

#### Ingestion Usecase
    - Business Logic For ingestion By calling ingestion method exposed by LightRAG repository

#### Retrieval Usecase
    - Business Logic For retrieval by calling retrieve method exposed by LightRAG repository

## Interface
    - exposed interfaces 
        "ingestion": if document_id is exist , it reingest 
        "retrieve" : retrieve context

### Domain

#### Entities
    - Base Model 
        {   
            id : uuid
            created_at: datetime
            created_by: uuid  (referent to user id, default to uuid.Nil)
            updated_at: datedtime
            updated_by: uuid  (referent to user id, uuid.Nil)
            deleted_at: datetime
            deleted_by: uuid  (referent to user id, uuid.Nil)
        }

    - Data Source Model (extend base model)
        {
            name: enum (google_drive, one_drive, ms_share_point, Default to GoogleDrive)
        }

    - Document Model (extend base model)
        {
            data_source_id : uuid (reference to data source model id)
            document_type : enum (pdf, md, xlsx, doc, ...)
        }
        
    - Chunk Model (extend base model)
        {
            document_id: uuid (reference to document model id)
            locator: json { page: number?, header_path: string?}
            length: number
            content: string
            validTil: datetime?
        }

    - Vector Model
        {
            chunk_id: uuid (reference to chunk model id) 
        }

    - Entity Model (graph entity)
        {
            name: string
            description: string
            metadata: json
            reference : string?
        }

    - Relationship Model (graph relationship)
        {
            name: string
            description: string
            metadata: json
            reference: string?
        }


