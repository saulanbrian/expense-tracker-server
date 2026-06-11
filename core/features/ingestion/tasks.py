import inspect
from os import pipe
from .pipeline import IngestionPipeline
from enum import Enum
import asyncio

import json


class PipelineStage(str, Enum):
    RETRIEVING = "retrieving_document_information"
    ANALYZING = "analyzing_document"
    EXTRACTING = "extracting_data"
    DRAFTING = "drafting_document"


class StageStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


async def ingest_document(ctx, document_id: str):
    pipeline = IngestionPipeline(ctx, document_id)
    current_stage = PipelineStage.RETRIEVING

    ##sleep for debugging
    await asyncio.sleep(5)

    async def send_stage_status(section_name: str, status: StageStatus):
        await ctx["redis"].publish(
            ctx["job_id"],
            json.dumps(
                {
                    "pipeline_stage": section_name,
                    "stage_status": status,
                }
            ),
        )

    async def run_stage(stage: PipelineStage, func, *args, **kwargs):
        current_stage = stage
        await send_stage_status(stage.value, StageStatus.IN_PROGRESS)
        res = func(*args, **kwargs)
        if inspect.isawaitable(res):
            res = await res
        await send_stage_status(stage.value, StageStatus.COMPLETED)
        return res

    async def retrieving_stage():
        should_continue = await pipeline.retrieve_and_lock()
        return should_continue

    async def analyzing_stage():
        await pipeline.download()
        await pipeline.convert()

    async def extracting_stage():
        await pipeline.extract_and_structure()

    async def drafting_stage():
        await pipeline.save_to_db()

    try:
        ##RETRIEVING  STAGE
        should_continue = await run_stage(PipelineStage.RETRIEVING, retrieving_stage)

        if not should_continue:
            await ctx["redis"].publish(
                ctx["job_id"],
                json.dumps(
                    {
                        "status": "ignored",
                        "reason": "document is either already ingested or ingestion already extracted",
                    }
                ),
            )
            return {"ingestion_status": "ignored"}

        ##ANALYZING  STAGE
        await run_stage(PipelineStage.ANALYZING, analyzing_stage)

        ##EXTRACTING  STAGE
        await run_stage(PipelineStage.EXTRACTING, extracting_stage)

        ##DRAFTING  STAGE
        await run_stage(PipelineStage.DRAFTING, drafting_stage)

        return {"ingestion_status": "success"}

    except Exception as e:
        await send_stage_status(current_stage.value, StageStatus.FAILED)
        return {
            "ingestion_status": "failed",
            "error_stage": current_stage.value,
            "error_step": pipeline.current_step,
        }
