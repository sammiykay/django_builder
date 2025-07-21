export const getLanguageFromFileName = (fileName: string): string => {
  if (!fileName) return 'plaintext';
  
  const ext = fileName.split('.').pop()?.toLowerCase();
  
  switch (ext) {
    // Python
    case 'py':
    case 'pyw':
    case 'pyi':
      return 'python';
    
    // JavaScript
    case 'js':
    case 'mjs':
      return 'javascript';
    
    // TypeScript
    case 'ts':
      return 'typescript';
    
    // JSX/TSX
    case 'jsx':
      return 'javascript';
    case 'tsx':
      return 'typescript';
    
    // HTML
    case 'html':
    case 'htm':
      return 'html';
    
    // CSS
    case 'css':
      return 'css';
    case 'scss':
    case 'sass':
      return 'scss';
    case 'less':
      return 'less';
    
    // JSON
    case 'json':
      return 'json';
    
    // XML
    case 'xml':
    case 'xsl':
    case 'xsd':
      return 'xml';
    
    // YAML
    case 'yml':
    case 'yaml':
      return 'yaml';
    
    // Markdown
    case 'md':
    case 'markdown':
      return 'markdown';
    
    // SQL
    case 'sql':
      return 'sql';
    
    // Shell scripts
    case 'sh':
    case 'bash':
    case 'zsh':
      return 'shell';
    
    // Docker
    case 'dockerfile':
      return 'dockerfile';
    
    // PHP
    case 'php':
    case 'phtml':
      return 'php';
    
    // Java
    case 'java':
      return 'java';
    
    // C/C++
    case 'c':
      return 'c';
    case 'cpp':
    case 'cc':
    case 'cxx':
      return 'cpp';
    case 'h':
    case 'hpp':
      return 'c';
    
    // C#
    case 'cs':
      return 'csharp';
    
    // Go
    case 'go':
      return 'go';
    
    // Rust
    case 'rs':
      return 'rust';
    
    // Ruby
    case 'rb':
      return 'ruby';
    
    // R
    case 'r':
      return 'r';
    
    // Swift
    case 'swift':
      return 'swift';
    
    // Kotlin
    case 'kt':
    case 'kts':
      return 'kotlin';
    
    // Scala
    case 'scala':
      return 'scala';
    
    // Configuration files
    case 'ini':
    case 'cfg':
    case 'conf':
      return 'ini';
    
    case 'toml':
      return 'toml';
    
    // Text files
    case 'txt':
    case 'log':
      return 'plaintext';
    
    default:
      // Special file names
      if (fileName.toLowerCase() === 'dockerfile') return 'dockerfile';
      if (fileName.toLowerCase() === 'makefile') return 'makefile';
      if (fileName.toLowerCase() === 'cmakelists.txt') return 'cmake';
      if (fileName.toLowerCase().startsWith('.env')) return 'dotenv';
      if (fileName.toLowerCase() === 'requirements.txt') return 'plaintext';
      if (fileName.toLowerCase() === 'package.json') return 'json';
      if (fileName.toLowerCase() === 'tsconfig.json') return 'json';
      if (fileName.toLowerCase().endsWith('.config.js')) return 'javascript';
      
      return 'plaintext';
  }
};

export const getEditorTheme = (): string => {
  return 'vs-dark'; // Can be configured based on user preference
};

export const getEditorOptions = (language: string) => {
  const baseOptions = {
    fontSize: 14,
    fontFamily: 'Consolas, "Courier New", monospace',
    lineNumbers: 'on' as const,
    roundedSelection: false,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    minimap: { enabled: true },
    wordWrap: 'on' as const,
    formatOnPaste: true,
    formatOnType: true,
    suggestOnTriggerCharacters: true,
    acceptSuggestionOnEnter: 'on' as const,
    tabCompletion: 'on' as const,
    quickSuggestions: {
      other: true,
      comments: true,
      strings: true
    },
    folding: true,
    foldingStrategy: 'auto' as const,
    showFoldingControls: 'always' as const,
    bracketPairColorization: {
      enabled: true
    }
  };

  // Language-specific options
  switch (language) {
    case 'python':
      return {
        ...baseOptions,
        tabSize: 4,
        insertSpaces: true,
        detectIndentation: false,
        trimAutoWhitespace: true,
      };
    
    case 'javascript':
    case 'typescript':
    case 'json':
      return {
        ...baseOptions,
        tabSize: 2,
        insertSpaces: true,
        detectIndentation: false,
      };
    
    case 'html':
    case 'css':
    case 'scss':
      return {
        ...baseOptions,
        tabSize: 2,
        insertSpaces: true,
        detectIndentation: false,
      };
    
    case 'yaml':
      return {
        ...baseOptions,
        tabSize: 2,
        insertSpaces: true,
        detectIndentation: false,
        trimAutoWhitespace: true,
      };
    
    default:
      return baseOptions;
  }
};

export const isEditableFile = (fileName: string): boolean => {
  const ext = fileName.split('.').pop()?.toLowerCase();
  
  // List of editable file extensions
  const editableExtensions = [
    'py', 'js', 'ts', 'jsx', 'tsx', 'html', 'htm', 'css', 'scss', 'sass', 'less',
    'json', 'xml', 'yml', 'yaml', 'md', 'markdown', 'sql', 'sh', 'bash', 'zsh',
    'php', 'java', 'c', 'cpp', 'cc', 'cxx', 'h', 'hpp', 'cs', 'go', 'rs', 'rb',
    'r', 'swift', 'kt', 'kts', 'scala', 'ini', 'cfg', 'conf', 'toml', 'txt',
    'log', 'env'
  ];
  
  // Special file names
  const editableFileNames = [
    'dockerfile', 'makefile', 'cmakelists.txt', 'requirements.txt',
    'package.json', 'tsconfig.json', '.gitignore', '.env'
  ];
  
  return editableExtensions.includes(ext || '') || 
         editableFileNames.some(name => fileName.toLowerCase().includes(name.toLowerCase()));
};