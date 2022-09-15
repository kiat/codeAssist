import React from "react";
import { useState } from "react";
import axios from "axios"

const FileUpload = () => {

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
            <div id="form">
                <form onSubmit={uploadFile} encType="multipart/form-data">
                    <div id="dockerfile">
                        <p className="inline">Select assignment</p>
                        <select className="inline">
                            <option value="test">test</option>
                        </select>
                    </div>
                    <div id="file">
                        <p className="inline">Choose file</p>
                        <input id="fileUpload" type="file" name="file" onChange={e => setFile(e.target.files[0])}/>
                        <input id="submit" type="submit"/>
                    </div>
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