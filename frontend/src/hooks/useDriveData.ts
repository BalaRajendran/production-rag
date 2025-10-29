import { useState, useEffect } from 'react';
import { supabase, DriveFile, QuickAccessFolder } from '../lib/supabase';

export function useDriveData() {
  const [files, setFiles] = useState<DriveFile[]>([]);
  const [folders, setFolders] = useState<QuickAccessFolder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const { data: filesData } = await supabase
        .from('files')
        .select('*')
        .order('last_modified', { ascending: false });

      const { data: foldersData } = await supabase
        .from('quick_access_folders')
        .select(`
          *,
          members:folder_members(*)
        `)
        .order('created_at', { ascending: false });

      if (filesData) setFiles(filesData);
      if (foldersData) setFolders(foldersData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }

  return {
    files,
    folders,
    loading,
    refresh: loadData,
  };
}
