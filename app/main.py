import streamlit as st
from dicomfile import DicomFile
import numpy as np
import traceback

def main():
    st.title("DICOM Modifier")
    st.subheader("A Simple interface for updating DICOM Tags.")
    st.write("Please upload a DICOM file to get started.")
    uploaded_file = st.file_uploader("Upload DICOM file")
    if uploaded_file is not None:
        dicom_file = DicomFile(uploaded_file)
    upload_container = st.container()
    with upload_container:
        upload,_,preview = st.columns([1,.2,1])
    with upload:
        try:
            st.image(dicom_file.extract_image(), caption="DICOM Image")
        except:
            try:
                image_stack = dicom_file.extract_image()
                slice_index = st.slider('Slice index', 0, image_stack.shape[0] - 1, image_stack.shape[0] // 2)
                st.image(image_stack[slice_index, :, :], caption=f"DICOM Image (slice {slice_index})")
            except:
                st.write("No image found")


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
            traceback.print_exc()

    if tags:
        output_path = st.text_input("Enter output path")
        if st.button("Save"):
            dicom_file.modify_and_save_dicom_file(updated_tags, output_path)
            st.success("File saved successfully")

if __name__ == "__main__":
    main()
