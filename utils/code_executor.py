import os
import tempfile
import uuid
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", "")
)


def execute_visualization_code(code: str) -> Dict[str, Any]:
    """
    Execute visualization code in a safe environment and return the results.

    Args:
        code (str): Python code to execute

    Returns:
        Dict containing:
            - success (bool): Whether execution was successful
            - output (str): Output message
            - file_paths (list): List of generated file paths
            - error (str): Error message if execution failed
            - temp_dir (str): Path to temporary directory containing the files
    """
    try:
        # Create a temporary directory for storing generated files
        temp_dir = tempfile.mkdtemp()
        os.makedirs(temp_dir, exist_ok=True)  # Ensure directory exists

        # Create a new namespace for execution
        namespace = {
            "plt": plt,
            "sns": sns,
            "pd": pd,
            "np": np,
            "os": os,
            "tempfile": tempfile,
            "uuid": uuid,
            "temp_dir": temp_dir,
        }

        # Execute the code
        exec(code, namespace)

        # Get all generated files
        generated_files = []
        for file in os.listdir(temp_dir):
            if file.endswith((".png", ".jpg", ".jpeg", ".svg", ".pdf")):
                file_path = os.path.join(temp_dir, file)
                generated_files.append(file_path)

        if not generated_files:
            return {
                "success": False,
                "output": "No visualization files were generated",
                "file_paths": [],
                "error": "No visualization files were generated",
                "temp_dir": temp_dir,
            }

        return {
            "success": True,
            "output": f"Successfully generated {len(generated_files)} visualization(s)",
            "file_paths": generated_files,
            "error": None,
            "temp_dir": temp_dir,
        }

    except Exception as e:
        return {
            "success": False,
            "output": "Failed to execute visualization code",
            "file_paths": [],
            "error": str(e),
            "temp_dir": None,
        }


def upload_to_supabase(
    file_path: str, metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Upload a file to Supabase Storage and store its metadata.

    Args:
        file_path (str): Path to the file to upload
        metadata (Dict, optional): Additional metadata to store

    Returns:
        Dict containing:
            - success (bool): Whether upload was successful
            - url (str): Public URL of the uploaded file
            - error (str): Error message if upload failed
    """
    try:
        # Generate a unique filename
        file_ext = os.path.splitext(file_path)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        # Upload file to Supabase Storage
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Upload to 'visualizations' bucket
        result = supabase.storage.from_("visualizations").upload(
            unique_filename,
            file_data,
            {"content-type": f"image/{file_ext[1:]}", "x-upsert": "true"},
        )

        # Get the public URL
        url = supabase.storage.from_("visualizations").get_public_url(unique_filename)

        # Store metadata in the database if provided
        if metadata:
            supabase.table("visualization_metadata").insert(
                {"file_name": unique_filename, "url": url, "metadata": metadata}
            ).execute()

        return {"success": True, "url": url, "error": None}

    except Exception as e:
        print(f"File path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        print(
            f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'}"
        )
        return {"success": False, "url": None, "error": str(e)}


def execute_and_upload(code: str, metadata: dict) -> dict:
    """Execute visualization code and upload generated files to Supabase."""
    temp_dir = None
    try:
        # Execute the code and get the result
        result = execute_visualization_code(code)
        temp_dir = result.get("temp_dir")

        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "output": result["output"],
            }

        # Upload each generated file
        urls = []
        for file_path in result["file_paths"]:
            if os.path.exists(file_path):
                # Upload to Supabase
                upload_result = upload_to_supabase(file_path, metadata)
                if upload_result["success"]:
                    urls.append(upload_result["url"])
                else:
                    print(f"Failed to upload {file_path}: {upload_result['error']}")

        if not urls:
            return {
                "success": False,
                "error": "No files were successfully uploaded",
                "output": result["output"],
            }

        return {"success": True, "urls": urls, "output": result["output"]}

    except Exception as e:
        print(f"Error in execute_and_upload: {str(e)}")
        return {"success": False, "error": str(e), "output": None}
    finally:
        # Only clean up temp directory if we're not in a test environment
        if temp_dir and os.getenv("TESTING") != "true":
            try:
                import shutil

                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp directory: {str(e)}")


if __name__ == "__main__":
    # Example usage
    test_code = """import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('Sine Wave')
plt.savefig(os.path.join(temp_dir, 'test.png'))"""

    result = execute_and_upload(
        test_code, {"title": "Sine Wave Visualization", "type": "line_plot"}
    )

    print("Execution and upload result:", result)
