import streamlit as st
from dicomfile import DicomFile
import numpy as np
import cv2
import traceback
from pydicom.filebase import DicomBytesIO
import openai
from pydicom.encaps import encapsulate

def main():
    st.set_page_config(layout="wide")
    st.title("DICOM Modifier")
    st.subheader("A Simple interface for updating DICOM Tags.")
    st.write("")


    if not 'dataset' in st.session_state:
        st.session_state.dataset = None
    if not 'filepath' in st.session_state:
        st.session_state.filepath = None
    if not 'tags' in st.session_state:
        st.session_state.tags = None



    ucol1,ucol2,ucol3 = st.columns([1,1,1])
    with ucol2:
        uploaded_file = st.file_uploader("Please upload a DICOM file to get started.")
    st.divider()
    if uploaded_file is not None:
        dicom_file = DicomFile(uploaded_file)
        upload_container = st.container()
        with upload_container:
            upload,_,preview = st.columns([1,.2,1])
        with upload:
            try:
                st.write("DICOM Image Preview")
                dicom_file.display_image(dicom_file)
                # Check if the user wants to modify the DICOM image
                if st.checkbox("Modify DICOM Image to Hide Sensitive Information"):
                    # Display the DICOM image for the user to select a region
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.checkbox("invert"):
                            image_data =dicom_file.extract_image()
                            st.image(image_data, caption="DICOM Image")
                        else:
                            image_data = cv2.cvtColor(dicom_file.extract_image(), cv2.COLOR_YCrCb2BGR)
                            st.image(image_data, caption="DICOM Image")
                    with col2:
                        st.write("Select a region and choose a background color to hide sensitive information.")
                        # Get the coordinates of the region selected by the user
                        x1 = st.number_input("Start X Coordinate", 0, dicom_file.dataset.Columns, value=10)
                        y1 = st.number_input("Start Y Coordinate", 0, dicom_file.dataset.Rows, value=76)
                        x2 = st.number_input("End X Coordinate", x1+300, dicom_file.dataset.Columns)
                        y2 = st.number_input("End Y Coordinate", y1+50, dicom_file.dataset.Rows)
                        # Get the background color selected by the user
                        bg_color = st.color_picker("Background Color")
                        # Convert the DICOM image to RGB format
                        image_data = cv2.cvtColor(dicom_file.extract_image(), cv2.COLOR_YCrCb2BGR)
                        # Apply the selected color over the selected region
                        image_data[y1:y2, x1:x2] = np.array(
                            [int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)])
                        # Update the pixel data of the DICOM dataset
                        dicom_file.dataset.PixelData = image_data.tobytes()
                        # Display the modified DICOM image
                        st.image(image_data, caption="Modified DICOM Image")



            except:
                st.write("Image Could Not Be Rendered")
                traceback.print_exc()

        with preview:
            header,reset = st.columns([1,1])
            with header:
                st.write("DICOM tags")



            try:
                tags = dicom_file.extract_tags()
                #print(tags)
                # if PatientName is in tags, then check if it is a string, if not, convert to a string
                # if PatientName is not in tags, then add it to tags with a value of 'None'
                if 'PatientName' in tags:
                    if not isinstance(tags['PatientName'], str):
                        tags['PatientName'] = str(tags['PatientName'])
                patientNamePreview = st.empty()
                patientNamePreview.write(f'Current Patient Name: {tags["PatientName"]}')
                # Check if we have a stored name
                if 'anonymized_name' not in st.session_state:
                    st.session_state.anonymized_name = ''

                # UI components for anonymization
                anonymize_container = st.container()
                with anonymize_container:
                    st.write("Anonymize DICOM")
                    col1, col2, col3 = st.columns(3)
                    # Text input for manual name entry
                    col1.divider()
                    entered_name = col1.text_input("Enter a new name to use:", st.session_state.anonymized_name)
                    st.session_state.anonymized_name = entered_name

                    editable_tags = {tag: value for tag, value in tags.items() if isinstance(value, (str, int, float))}
                    # Button to generate a random name
                    col2.divider()
                    if col1.button("Generate Random Name"):
                        # Here, we generate a random name using any method of your choice.
                        # For simplicity, I'm just using a random number. Replace this with a name generator if you have one.
                        generated_name = f"Patient^{np.random.randint(1000, 9999)}"
                        st.session_state.anonymized_name = generated_name
                        # rerun the text input with the new name
                        #st.experimental_rerun()

                    # Button to apply the name to the DICOM file
                    col3.divider()
                    if col1.button("Apply Name"):
                        st.session_state.anonymized_name = entered_name
                        tags['PatientName'] = st.session_state.anonymized_name
                        editable_tags['PatientName'] = st.session_state.anonymized_name
                        dicom_file.modify_tags({"PatientName": st.session_state.anonymized_name})
                        patientNamePreview.write(f'Current Patient Name: {st.session_state.anonymized_name}')
                        st.session_state.tags = tags



                updated_tags = st.data_editor(editable_tags)
                if st.session_state.anonymized_name != None:
                    updated_tags['PatientName'] = st.session_state.anonymized_name

                    print(f'updated tags: {updated_tags}')

                dicom_file.modify_tags(updated_tags)
                filename = f'{dicom_file.dataset.get("PatientName")}-{dicom_file.dataset.get("StudyDate")}-{dicom_file.dataset.get("ManufacturerModelName")}-{dicom_file.dataset.get("ImageLaterality")}.dcm'
                print(f"Saving DICOM file to {filename}")


            except:
                st.write("No tags found")
                tags = None
                traceback.print_exc()
        try:
            if tags:
                output_path = st.text_input("Enter output path", filename)
                if st.button("Save"):
                    dataset, filepath = dicom_file.modify_and_save_dicom_file(updated_tags, output_path)
                    st.session_state.dataset = dataset
                    st.session_state.filepath = filepath
                    st.success("File saved successfully")
                if st.session_state.dataset is not None:
                    dataset = st.session_state.dataset
                    output_path = st.session_state.filepath
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

    #st._rerun()

if __name__ == "__main__":
    main()
