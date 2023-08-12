from pydicom.tag import Tag
import cv2
import traceback
import pydicom
import numpy as np
import streamlit as st

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
            filename = self.dataset.get("PatientName", "anonymous.dcm")

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

    def ybr_to_rgb(self,image_data):
        if image_data.shape[2] == 3:
            return cv2.cvtColor(image_data, cv2.COLOR_YCrCb2BGR)
        return image_data

    def display_image(self,dicom_file):
        try:
            image_data = dicom_file.extract_image()

            # Normalize the pixel values
            #image_data = (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data))
            #image_data = (image_data * 255).astype(np.uint8)

            # Check if the image is grayscale
            if len(image_data.shape) == 2 or image_data.shape[2] == 1:
                image_data = np.stack([image_data] * 3, axis=-1)  # Convert grayscale to RGB
            else:
                # Convert YBR to RGB if necessary
                photometric_interpretation = dicom_file.dataset.get("PhotometricInterpretation", None)
                print(f'photometric interpretation: {photometric_interpretation}')
                if photometric_interpretation == "YBR_FULL_422":
                    print('converting to rgb')
                    image_data = self.ybr_to_rgb(image_data)
                if photometric_interpretation == "MONOCHROME1":
                    image_data = np.max(image_data) - image_data
                if photometric_interpretation == "MONOCHROME2":
                    image_data = image_data
                if photometric_interpretation == "RGB":
                    if st.checkbox("invert"):
                        image_data = image_data
                    else:
                        image_data = self.ybr_to_rgb(image_data)

            st.image(image_data, caption="DICOM Image")

        except:
            traceback.print_exc()
            # Handle multiple slices if the DICOM file is a 3D volume

            try:
                image_stack = dicom_file.extract_image()
                image_stack = (image_stack - np.min(image_stack)) / (
                        np.max(image_stack) - np.min(image_stack))
                slice_index = st.slider('Slice index', 0, image_stack.shape[0], image_stack.shape[0] // 255)
                st.image(image_stack[slice_index, :, :], caption=f"DICOM Image (slice {slice_index})", clamp=True)
            except:
                st.write("No image found")
                traceback.print_exc()
                try:
                    image_stack = dicom_file.extract_image()
                    slice_index = st.slider('Slice index3', 0, image_stack.shape[0] - 1, image_stack.shape[0] // 2)
                    st.image(image_stack[slice_index, :, :], caption=f"DICOM Image (slice {slice_index})",
                             clamp=True)
                except:
                    traceback.print_exc()

