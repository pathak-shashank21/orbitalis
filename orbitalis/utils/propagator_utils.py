
def safe_filename(name: str) -> str:
    return (
        name.replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("-", "_")
            .replace("/", "_")
    )
