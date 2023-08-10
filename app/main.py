import streamlit as st
from dicomfile import DicomFile
import numpy as np
import traceback
from pydicom.filebase import DicomBytesIO
import cv2

def main():
    st.set_page_config(layout="wide")
    st.title("DICOM Modifier")
    st.subheader("A Simple interface for updating DICOM Tags.")
    st.write("Please upload a DICOM file to get started.")

    def ybr_to_rgb(image_data):
        if image_data.shape[2] == 3:
            return cv2.cvtColor(image_data, cv2.COLOR_YCrCb2BGR)
        return image_data

    def display_image(dicom_file):
        try:
            image_data = dicom_file.extract_image()

            # Normalize the pixel values
            #image_data = (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data))
           # image_data = (image_data * 255).astype(np.uint8)

            # Check if the image is grayscale
            if len(image_data.shape) == 2 or image_data.shape[2] == 1:
                image_data = np.stack([image_data] * 3, axis=-1)  # Convert grayscale to RGB
            else:
                # Convert YBR to RGB if necessary
                #photometric_interpretation = dicom_file.get("PhotometricInterpretation", "").value
                #if photometric_interpretation == "YBR_FULL_422":
                image_data = ybr_to_rgb(image_data)

            st.image(image_data, caption="DICOM Image")

        except:
            traceback.print_exc()
            # Handle multiple slices if the DICOM file is a 3D volume
            try:
                slice_index = st.slider('Slice index', 0, image_data.shape[0] - 1, image_data.shape[0] // 2)
                st.image(image_data[slice_index, :, :], caption=f"DICOM Image (slice {slice_index})")
            except:
                st.write("Error displaying image")
                traceback.print_exc()

    if not 'dataset' in st.session_state:
        st.session_state.dataset = None
    if not 'filepath' in st.session_state:
        st.session_state.filepath = None

    uploaded_file = st.file_uploader("Upload DICOM file")
    if uploaded_file is not None:
        dicom_file = DicomFile(uploaded_file)
        upload_container = st.container()
        with upload_container:
            upload,_,preview = st.columns([1,.2,1])
        with upload:
            try:
                display_image(dicom_file)
            except:
                try:
                    image_stack = dicom_file.extract_image()
                    slice_index = st.slider('Slice index', 0, image_stack.shape[0] - 1, image_stack.shape[0] // 2)
                    st.image(image_stack[slice_index, :, :], caption=f"DICOM Image (slice {slice_index})")

                except:
                    st.write("No image found")
                    traceback.print_exc()
                    try:
                        image_stack = dicom_file.extract_image()
                        image_stack = (image_stack - np.min(image_stack)) / (
                                    np.max(image_stack) - np.min(image_stack))
                        slice_index = st.slider('second Slice index', 0, image_stack.shape[0] , image_stack.shape[0] // 255)
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

        with preview:
            st.write("DICOM tags")
            try:
                tags = dicom_file.extract_tags()
                #print(tags)
                # if PatientName is in tags, then check if it is a string, if not, convert to a string
                # if PatientName is not in tags, then add it to tags with a value of 'None'
                if 'PatientName' in tags:
                    if not isinstance(tags['PatientName'], str):
                        tags['PatientName'] = str(tags['PatientName'])
                editable_tags = {tag: value for tag, value in tags.items() if isinstance(value, (str, int, float))}
                #
                updated_tags = st.data_editor(editable_tags)
                dicom_file.modify_tags(updated_tags)


            except:
                st.write("No tags found")
                tags = None
                traceback.print_exc()
        try:
            if tags:
                output_path = st.text_input("Enter output path")
                if st.button("Save"):
                    dataset, filepath = dicom_file.modify_and_save_dicom_file(updated_tags, output_path)
                    st.session_state.dataset = dataset
                    st.session_state.filepath = filepath
                    st.success("File saved successfully")
                if st.session_state.dataset is not None:
                    dataset = st.session_state.dataset
                    filepath = st.session_state.filepath
                    with DicomBytesIO() as f:
                        dataset.save_as(f, write_like_original=True)
                        dicom_bytes = f.parent.getvalue()
                    if st.download_button("Download", data=dicom_bytes, file_name=output_path, mime='application/octet-stream'):
                        st.success("File downloaded successfully")
            else:
                st.write("No Tags found, Upload a DICOM file to get started")
                traceback.print_exc()
        except:
            traceback.print_exc()
            st.write("No Tags found, Upload a DICOM file to get started")

if __name__ == "__main__":
    main()
