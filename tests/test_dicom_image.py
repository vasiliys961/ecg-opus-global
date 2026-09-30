import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid

from backend.dicom_image import DicomOpenError, open_dicom_image


def _save(path, dataset) -> None:
    dataset.is_little_endian = True
    dataset.is_implicit_VR = False
    dataset.save_as(path, write_like_original=False)


def _file_meta():
    meta = Dataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    return meta


def test_dicom_image_becomes_png(tmp_path):
    path = tmp_path / "sheet.dcm"
    dataset = FileDataset(str(path), {}, file_meta=_file_meta(), preamble=b"\0" * 128)
    dataset.SOPClassUID = dataset.file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = dataset.file_meta.MediaStorageSOPInstanceUID
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.Rows = 8
    dataset.Columns = 8
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.PixelData = np.arange(64, dtype=np.uint8).tobytes()
    _save(path, dataset)

    png = open_dicom_image(path.read_bytes())

    assert png.startswith(b"\x89PNG")


def test_dicom_waveform_is_not_drawn(tmp_path):
    path = tmp_path / "wave.dcm"
    dataset = FileDataset(str(path), {}, file_meta=_file_meta(), preamble=b"\0" * 128)
    dataset.SOPClassUID = dataset.file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = dataset.file_meta.MediaStorageSOPInstanceUID
    dataset.WaveformSequence = [Dataset()]
    _save(path, dataset)

    try:
        open_dicom_image(path.read_bytes())
    except DicomOpenError as exc:
        assert "кривая" in str(exc)
    else:
        raise AssertionError("кривая не должна стать снимком")
