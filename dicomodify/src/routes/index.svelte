<script>
    let file;
    let tags = [];
    let isLoading = false;
  
    async function uploadDicom() {
      isLoading = true;
      const formData = new FormData();
      formData.append('file', file);
  
      try {
        const response = await fetch('http://localhost:8000/upload-dicom/', {
          method: 'POST',
          body: formData,
        });
  
        if (response.ok) {
          const data = await response.json();
          tags = data.tags; // Assuming the API returns the tags in this format
          isLoading = false;
        } else {
          console.error('Error uploading file');
          isLoading = false;
        }
      } catch (error) {
        console.error('Error:', error);
        isLoading = false;
      }
    }
    let modifiedTags = {};
  async function modifyTags() {
    isLoading = true;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tags', JSON.stringify(modifiedTags));

    try {
      const response = await fetch('http://localhost:8000/modify-tags/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const modifiedFileBlob = await response.blob();
        const modifiedFileUrl = URL.createObjectURL(modifiedFileBlob);
        downloadFile(modifiedFileUrl, "modified.dcm");
        isLoading = false;
      } else {
        console.error('Error modifying tags');
        isLoading = false;
      }
    } catch (error) {
      console.error('Error:', error);
      isLoading = false;
    }
  }

  function downloadFile(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
</script>

{#if tags.length > 0}
  
  <div>
    <input type="file" accept=".dcm" on:change="{(event) => file = event.target.files[0]}" />
    <button on:click="{uploadDicom}" class="btn btn-primary" disabled={isLoading}>
      {#if isLoading}
        Uploading...
      {:else}
        Upload DICOM File
      {/if}
    </button>
  
    {#if tags.length > 0}
      <div class="tags-display">
        <h3>Extracted Tags:</h3>
        <pre>{JSON.stringify(tags, null, 2)}</pre>
      </div>
    {/if}
  </div>
  
  <div class="modify-tags-form">
    <h3>Modify Tags:</h3>
    <input type="text" placeholder="Patient Name" bind:value="{modifiedTags.PatientName}" />
    <button on:click="{modifyTags}" class="btn btn-secondary" disabled={isLoading || !file}>
      {#if isLoading}
        Modifying...
      {:else}
        Modify and Download
      {/if}
    </button>
  </div>
{/if}

<style>
    .tags-display {
      margin-top: 1rem;
      padding: 1rem;
      background-color: #f3f3f3;
      border-radius: 8px;
    }
    .modify-tags-form {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  </style>