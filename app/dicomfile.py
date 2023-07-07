from pydicom.tag import Tag

import traceback
import pydicom

class DicomFile:
    def __init__(self, file):
        self.file = file
        self.dataset = self.read_file()

    def read_file(self):
        return pydicom.dcmread(self.file)

    def extract_image(self):
        return self.dataset.pixel_array

    def extract_tags(self):
        return {tag: self.dataset[tag].value for tag in self.dataset.dir()}

    def modify_and_save_dicom_file(self, updated_tags, output_path):
        try:
            # Modify the DICOM tags
            for tag, value in updated_tags.items():
                print(f'this is the  tag {tag}')
                print(type(tag))
                if tag in self.dataset:
                    if tag == "(0018, 9073)" or tag == "AcquisitionDuration":  # Acquisition Duration
                        value = float(value)
                if tag in ('DepthSpatialResolution',"AcquisitionDuration",'MaximumDepthDistortion','AlongScanSpatialResolution','AcrossScanSpatialResolution','IlluminationBandwidth','IlluminationPower','IlluminationWaveLength','MaximumAcrossScanDistortion','MaximumAlongScanDistortion','MaximumDepthDistortion','HorizontalFieldOfView','RescaleIntercept','RescaleSlope'):
                    print(tag)# Acquisition Duration
                    value = float(value)
                    print(f'VALUE: {value}')
                if tag in('InConcatenationNumber','InConcatenationTotalNumber','ConcatenationFrameOffsetNumber','BitsAllocated','BitsStored','Columns','ConcatenationFrameOffsetNumber','HighBit','InstanceNumber','PixelRepresentation','Rows','SamplesPerPixel','SeriesNumber','SmallestImagePixelValue','LargestImagePixelValue','PlanarConfiguration','RepresentativeFrameNumber'):
                    print(tag)
                    value = int(value)
                    print(f'Value: {value}')
                if tag == 'FrameIncrementPointer':
                    print(tag)
                    print(f'why is this not working?? {value}')
                    # Remove parentheses and split the string into two parts
                    parts = value.strip('()').split(',')
                    # Convert each part from hexadecimal to integer
                    parts = [int(part, 16) for part in parts]
                    # Create a pydicom Tag object from the parts
                    value = Tag(tag)
                    print(f'Value: {value}')
                self.dataset[tag].value = value
            # Save the new DICOM file
            print(f"Saving DICOM file to {output_path}")
            print(f"saving {self.dataset} to {output_path}")
            self.dataset.save_as(output_path)
            return self.dataset, output_path
        except ValueError:
            print(f"Unable to set {tag} to {value}")
            print('this is the first fail')
            traceback.print_exc()
        except:
            print(f"Unable to save DICOM file issue with {tag} to {value}")
            traceback.print_exc()
            print('hey did this fucking work?')


    def modify_tags(self, updated_tags):
        for tag, value in updated_tags.items():
            try:
                if tag in self.dataset:
                    if tag == "(0018, 9073)":  # Acquisition Duration
                        value = float(value)
                    self.dataset[tag].value = value
            except ValueError:
                print(f"Unable to set {tag} to {value}")

    def write_file(self, output_path):
        self.dataset.save_as(output_path)
