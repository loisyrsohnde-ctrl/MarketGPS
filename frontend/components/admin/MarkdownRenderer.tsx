'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ node, ...props }) => (
          <h1 className="text-3xl font-bold mt-6 mb-4 text-slate-900 dark:text-slate-100" {...props} />
        ),
        h2: ({ node, ...props }) => (
          <h2 className="text-2xl font-bold mt-5 mb-3 text-slate-900 dark:text-slate-100" {...props} />
        ),
        h3: ({ node, ...props }) => (
          <h3 className="text-xl font-bold mt-4 mb-2 text-slate-900 dark:text-slate-100" {...props} />
        ),
        p: ({ node, ...props }) => (
          <p className="mb-4 text-slate-700 dark:text-slate-300 leading-relaxed" {...props} />
        ),
        ul: ({ node, ...props }) => (
          <ul className="list-disc list-inside mb-4 text-slate-700 dark:text-slate-300" {...props} />
        ),
        ol: ({ node, ...props }) => (
          <ol className="list-decimal list-inside mb-4 text-slate-700 dark:text-slate-300" {...props} />
        ),
        li: ({ node, ...props }) => (
          <li className="mb-2" {...props} />
        ),
        blockquote: ({ node, ...props }) => (
          <blockquote
            className="border-l-4 border-blue-500 pl-4 italic my-4 text-slate-600 dark:text-slate-400"
            {...props}
          />
        ),
        code: ({ node, ...props }) => {
          const isInline = !node?.position || (node?.data as any)?.meta === undefined;
          return isInline ? (
            <code
              className="bg-gray-200 dark:bg-slate-700 px-1.5 py-0.5 rounded text-sm font-mono text-slate-900 dark:text-slate-100"
              {...props}
            />
          ) : (
            <code className="block bg-gray-100 dark:bg-slate-700 p-3 rounded mb-4 overflow-x-auto text-sm font-mono text-slate-900 dark:text-slate-100" {...props} />
          );
        },
        a: ({ node, ...props }) => (
          <a
            className="text-blue-600 dark:text-blue-400 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
            {...props}
          />
        ),
        img: ({ node, ...props }) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            className="max-w-full h-auto rounded-lg my-4"
            {...props}
          />
        ),
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full border-collapse border border-gray-300 dark:border-slate-600" {...props} />
          </div>
        ),
        th: ({ node, ...props }) => (
          <th className="border border-gray-300 dark:border-slate-600 bg-gray-100 dark:bg-slate-700 px-4 py-2 text-left font-semibold text-slate-900 dark:text-slate-100" {...props} />
        ),
        td: ({ node, ...props }) => (
          <td className="border border-gray-300 dark:border-slate-600 px-4 py-2 text-slate-700 dark:text-slate-300" {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
