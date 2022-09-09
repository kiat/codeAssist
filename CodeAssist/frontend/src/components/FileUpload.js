import React from "react";
import { useState } from "react";
import axios from "axios"

const FileUpload = (props) => {

    const [file, setFile] = useState(null);
    const [response, setResponse] = useState(null);

    const uploadFile = async (e) => {
        e.preventDefault()
        const data = new FormData()

        data.append("file", file)
        const url = "http://localhost:5000/upload"
        const response = await axios.post(url, data, {})
        setResponse(response.data);
    }

    return (
        <div>
            <div>
                <form onSubmit={uploadFile} encType="multipart/form-data">
                    <input type="file" name="file" onChange={e => setFile(e.target.files[0])}/>
                    <input type="submit"/>
                </form>
            </div>
            <div>
                <h1>Results</h1>
                {response ? <pre>{response}</pre> : ""}
            </div>
        </div>
    )
}

export default FileUpload