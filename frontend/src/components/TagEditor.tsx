// src/components/TagEditor.tsx
import React, { useState, useEffect } from "react";
import { Autocomplete, TextField } from "@mui/material";
import { fetchTags, updateItemTags } from "../utils/api";

interface TagEditorProps {
  itemId: string;
  initialTags: string[];
}

const TagEditor: React.FC<TagEditorProps> = ({ itemId, initialTags }) => {
  const [options, setOptions] = useState<string[]>([]);
  const [value, setValue] = useState<string[]>(initialTags);

  useEffect(() => {
    fetchTags().then(setOptions).catch(console.error);
  }, []);

  const handleChange = (_: any, newTags: string[]) => {
    setValue(newTags);
    updateItemTags(itemId, newTags).catch(console.error);
  };

  return (
    <Autocomplete
      multiple
      freeSolo
      options={options}
      value={value}
      onChange={handleChange}
      renderInput={(params) => <TextField {...params} variant="standard" />}
      sx={{ width: "100%" }}
    />
  );
};

export default TagEditor;
