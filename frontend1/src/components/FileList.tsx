import { FileText, Image, FileSpreadsheet, File, MoreVertical, CloudOff } from 'lucide-react';
import { DriveFile } from '../lib/supabase';

interface FileListProps {
  files: DriveFile[];
}

const fileIcons: Record<string, any> = {
  doc: FileText,
  docx: FileText,
  txt: FileText,
  pdf: FileText,
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
  jpg: Image,
  jpeg: Image,
  png: Image,
  gif: Image,
};

export function FileList({ files }: FileListProps) {
  const getFileIcon = (type: string) => {
    const Icon = fileIcons[type.toLowerCase()] || File;
    return Icon;
  };

  const getIconColor = (type: string) => {
    const colors: Record<string, string> = {
      doc: 'text-blue-500',
      docx: 'text-blue-500',
      txt: 'text-blue-500',
      pdf: 'text-red-500',
      xlsx: 'text-green-500',
      xls: 'text-green-500',
      jpg: 'text-orange-500',
      jpeg: 'text-orange-500',
      png: 'text-orange-500',
    };
    return colors[type.toLowerCase()] || 'text-gray-500';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }) + ' - ' + date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-700 mb-4">ALL FILES</h2>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-[2fr,1fr,1fr,1fr,auto] gap-4 px-6 py-3 bg-gray-50 text-xs font-semibold text-gray-500 border-b border-gray-200">
          <div>NAME</div>
          <div>OWNER</div>
          <div>LAST MODIFIED</div>
          <div>FILE SIZE</div>
          <div></div>
        </div>
        <div className="divide-y divide-gray-100">
          {files.map((file) => {
            const Icon = getFileIcon(file.type);
            const iconColor = getIconColor(file.type);

            return (
              <div
                key={file.id}
                className="grid grid-cols-[2fr,1fr,1fr,1fr,auto] gap-4 px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer items-center"
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-5 h-5 ${iconColor}`} />
                  <span className="text-sm font-medium text-gray-700 truncate">{file.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-xs font-bold text-white">
                    A
                  </div>
                </div>
                <div className="text-sm text-gray-600">{formatDate(file.last_modified)}</div>
                <div className="text-sm text-gray-600 flex items-center gap-2">
                  {formatFileSize(file.size)}
                  <CloudOff className="w-4 h-4 text-gray-400" />
                </div>
                <button className="p-1 hover:bg-gray-200 rounded transition-colors">
                  <MoreVertical className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
