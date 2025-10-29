import { FileText } from 'lucide-react';

interface LastModifiedProps {
  fileName: string;
  date: string;
  avatarUrl?: string;
}

export function LastModified({ fileName, date, avatarUrl }: LastModifiedProps) {
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
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="text-xs font-semibold text-gray-500 mb-3">LAST MODIFIED</div>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
          <FileText className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-700 mb-1">{fileName}</div>
          <div className="text-xs text-gray-500">{formatDate(date)}</div>
        </div>
      </div>
    </div>
  );
}
