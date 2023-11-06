<script>


    let file;
    let tags = [];
    let isLoading = false;
    let parsedTags = [];
  
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
      console.log(data);
      console.log(data.tags);
      // Make sure to access the tags string with data.tags
      parsedTags = parseDicomTags(data.tags); // Use the string contained in data.tags
      console.log(parsedTags);
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

  function parseDicomTags(tagString) {
  const tagLines = tagString.split('\n'); // Split by new line
  const tags = [];

  for (const line of tagLines) {
    // Match lines that have the pattern (XXXX, XXXX) TAG_NAME VR: VALUE
    // The regex now handles multiple spaces and different characters in the tag name.
    // It also allows for different separators (like spaces or equals signs) between VR and the value.
    const match = line.match(/\(([\dA-F]{4}), ([\dA-F]{4})\) ([^\r\n]+?)\s+([A-Z]{2})\s*[:=]\s*(.+)/);
    if (match) {
      tags.push({
        group: match[1],
        element: match[2],
        tagName: match[3].trim(), // Trim to remove any extra spaces around the tag name
        vr: match[4],
        value: match[5].trim(), // Trim to remove any extra spaces around the value
      });
    }
  }

  console.log(tags);
  return tags;
}


  </script>


<div class = ''>
    <h1 class = 'text-transparent bg-clip-text bg-gradient-to-br  from-green-500 to-blue-500 text-3xl font-bold '>Dicom Modifier</h1>
    <p>upload and modify dicom tags</p>
    </div>

    <div class="flex flex-col items-center justify-center p-8">
        <div class="mb-4">
          <input
            type="file"
            accept=".dcm"
            class="block w-full text-sm text-slate-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-violet-50 file:text-violet-700
            hover:file:bg-violet-100"
            on:change="{(event) => file = event.target.files[0]}"
          />
        </div>
        <button
          on:click="{uploadDicom}"
          class="px-6 py-2 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300"
          disabled={isLoading}
        >
          {#if isLoading}
            Uploading...
          {:else}
            Upload DICOM File
          {/if}
        
      </div>
  
  
      {#if parsedTags.length > 0}
      <div class="overflow-x-auto relative shadow-md sm:rounded-lg m-8">
        <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
          <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
            <tr>
              <th scope="col" class="py-3 px-6">
                Tag Name
              </th>
              <th scope="col" class="py-3 px-6">
                Value
              </th>
            </tr>
          </thead>
        <tbody>
        {#each parsedTags as tag}
        <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
        <td class="py-4 px-6">
         {tag.tagName}
         </td>
        <td class="py-4 px-6">
        {tag.value}
        </td>
        </tr>
        {/each}
        </tbody>
        </table>
    
    <div class="flex flex-col p-8 space-y-4">
        <input
          type="text"
          placeholder="Patient Name"
          bind:value="{modifiedTags.PatientName}"
          class="block p-2.5 w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          on:click="{modifyTags}"
          class="px-6 py-2 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300"
          disabled={isLoading || !file}
        >
          {#if isLoading}
            Modifying...
          {:else}
            Modify and Download
          {/if}
        </button>
      </div>
    </div>
    {/if}

<style lang="postcss">
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


    :global(html) {
     
    }
 
  </style>