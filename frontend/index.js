let cwd = [];

async function fetchFolderContent(path) {
    return await (await fetch(`http://localhost:8080/list_dir?path=${path}`)).json();
}

function populateFolderTable(folderData) {
    const tableElement = document.querySelector("#files-list");
    folderData.files.forEach(fileData => {
        const row = document.createElement("tr");

        const filename = document.createElement("td");
        filename.innerText = fileData.name;

        const size = document.createElement("td");
        size.innerText = fileData.folder === true ? "Folder" : fileData.size;

        const created = document.createElement("td");
        created.innerText = fileData.created;

        if (fileData.folder === true) {
            filename.style.fontWeight = "bold";
            row.className = "folder-row";
            row.onclick = async () => {
                cwd.push(fileData.name)
                console.log(cwd.join("/"));
                initTable();
                const newFolderData = await fetchFolderContent(cwd.join("/"));
                populateFolderTable(newFolderData);
            }
        } else {
            row.className = "file-row";
        }

        row.appendChild(filename);
        row.appendChild(size);
        row.appendChild(created);
        row.appendChild(getFileFunctionButtons(fileData.name));
        tableElement.appendChild(row);
    });
}

function getFileFunctionButtons(fileName) {
    const td = document.createElement("td");

    const downloadBtn = document.createElement("button");
    downloadBtn.className = "btn-mini";

    const downloadIcon = document.createElement("span");
    downloadIcon.innerText = "download";
    downloadIcon.className = "material-symbols-outlined";
    downloadBtn.appendChild(downloadIcon);

    downloadBtn.onclick = async () => {
        downloadFile([...cwd, fileName].join("/"), fileName);
    };

    const editBtn = document.createElement("button");
    editBtn.className = "btn-mini";
    const editIcon = document.createElement("span");
    editIcon.innerText = "edit_document";
    editIcon.className = "material-symbols-outlined";
    editBtn.appendChild(editIcon);

    td.appendChild(downloadBtn);
    td.appendChild(editBtn);

    return td;
}

function initTable() {
    const table = document.querySelector("#files-list");
    table.innerHTML = "";

    if (cwd.length === 0) {
        return
    }

    const goUpFolderRow = document.createElement("tr");
    goUpFolderRow.className = "folder-row";

    const goUpFolderName = document.createElement("td")
    goUpFolderName.innerText = "..";
    goUpFolderName.style.fontWeight = "bold";

    goUpFolderRow.appendChild(goUpFolderName);

    goUpFolderRow.onclick = async () => {
        cwd.pop();
        await refresh();
    };

    table.appendChild(goUpFolderRow);
}

async function downloadFile(filePath, fileName) {
    try {
        const response = await fetch(`http://localhost:8080/file?path=${encodeURIComponent(filePath)}`);

        if (response.status === 200) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = fileName || "downloaded_file";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            const errorData = await response.json();
            console.error("Error downloading file:", errorData.message);
            alert(`Error: ${errorData.message}`);
        }
    } catch (error) {
        console.error("Unexpected error:", error);
        alert("An unexpected error occurred while downloading the file.");
    }
}

function clickInputElement() {
    document.querySelector("#file-input").click()
}

async function uploadFile() {
    const files = document.querySelector("#file-input").files;
    for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);
        await fetch(`http://localhost:8080/upload?path=${cwd.join("/")}`, {
            method: "POST",
            body: formData,
        })
    }

    await refresh();
}

async function refresh() {
    initTable();
    populateFolderTable(await fetchFolderContent(cwd.join("/")));
}

window.onload = async function() {
    await refresh();
}