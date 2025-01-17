from pathlib import Path
from types import SimpleNamespace
from typing import Dict

from fixtures import fixture
from virtool_workflow import hooks, step
from virtool_workflow.api.samples import SampleProvider


@fixture
def intermediate():
    return SimpleNamespace()


@step
async def download_raw_files(
    intermediate,
    sample_provider: SampleProvider,
    input_files: Dict[str, Path],
):
    """Download the read files which were uploaded by the user."""
    left = input_files.get("reads_1.fq.gz")

    intermediate.sample = await sample_provider.get()

    # Set the intermediate.sample path to be the download path
    intermediate.sample.path = left.parent

    return "Raw reads for intermediate.sample {sample.id} collected."


@step
async def run_fastqc(
    fastqc,
    intermediate,
):
    """
    Run `fastqc` on the read files. Parse the output
    into a dictionary and add it to the scope.
    """
    read_paths = [intermediate.sample.path/"reads_1.fq.gz"]
    if intermediate.sample.paired:
        read_paths.append(intermediate.sample.path/"reads_1.fq.gz")

    intermediate.quality = await fastqc(read_paths)

    return "Fastqc run completed."


@step
async def upload_read_files(intermediate, sample_provider: SampleProvider):
    """Upload the read files."""
    await sample_provider.upload(intermediate.sample.path/"reads_1.fq.gz")
    if intermediate.sample.paired:
        await sample_provider.upload(intermediate.sample.right/"reads_2.fq.gz")


@step
async def upload_quality(sample_provider: SampleProvider, intermediate):
    """Upload the resulting quality to the sample record."""
    await sample_provider.finalize(intermediate.quality)


@hooks.on_failure
async def delete_sample(sample_provider: SampleProvider):
    """Delete the sample in the case of a failure."""
    await sample_provider.delete()
