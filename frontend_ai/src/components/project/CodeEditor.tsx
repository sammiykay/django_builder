import React, { useRef, useEffect } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  fileName: string;
  readOnly?: boolean;
  onSave?: () => void;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language,
  fileName,
  readOnly = false,
  onSave
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

  // Update editor options when readOnly changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        readOnly: readOnly,
        formatOnPaste: !readOnly,
        formatOnType: !readOnly,
        suggestOnTriggerCharacters: !readOnly,
        acceptSuggestionOnEnter: readOnly ? 'off' : 'on',
        tabCompletion: readOnly ? 'off' : 'on',
        quickSuggestions: readOnly ? false : {
          other: true,
          comments: true,
          strings: true
        }
      });
    }
  }, [readOnly]);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Configure editor options
    editor.updateOptions({
      fontSize: 12,
      fontFamily: 'Consolas, "Courier New", monospace',
      lineNumbers: 'on',
      roundedSelection: false,
      scrollBeyondLastLine: false,
      readOnly: readOnly,
      automaticLayout: true,
      minimap: { enabled: true },
      scrollbar: {
        vertical: 'visible',
        horizontal: 'visible',
        useShadows: false,
        verticalHasArrows: false,
        horizontalHasArrows: false,
      },
      wordWrap: 'on',
      formatOnPaste: !readOnly,
      formatOnType: !readOnly,
      suggestOnTriggerCharacters: !readOnly,
      acceptSuggestionOnEnter: readOnly ? 'off' : 'on',
      tabCompletion: readOnly ? 'off' : 'on',
      quickSuggestions: readOnly ? false : {
        other: true,
        comments: true,
        strings: true
      }
    });

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      if (onSave) {
        onSave();
      }
    });

    // Configure Python-specific settings
    if (language === 'python') {
      monaco.languages.registerCompletionItemProvider('python', {
        provideCompletionItems: (model, position) => {
          const suggestions = [
            {
              label: 'def',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'def ${1:function_name}(${2:args}):\n    ${3:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Define a function'
            },
            {
              label: 'class',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'class ${1:ClassName}:\n    def __init__(self${2:, args}):\n        ${3:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Define a class'
            },
            {
              label: 'if',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'if ${1:condition}:\n    ${2:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'If statement'
            },
            {
              label: 'for',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'for ${1:item} in ${2:iterable}:\n    ${3:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'For loop'
            },
            {
              label: 'while',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'while ${1:condition}:\n    ${2:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'While loop'
            },
            {
              label: 'try',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'try:\n    ${1:pass}\nexcept ${2:Exception} as ${3:e}:\n    ${4:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Try-except block'
            }
          ];

          return { suggestions };
        }
      });
    }

    // Configure Django-specific completions for Python files
    if (language === 'python' && (fileName.includes('models.py') || fileName.includes('views.py') || fileName.includes('serializers.py'))) {
      monaco.languages.registerCompletionItemProvider('python', {
        provideCompletionItems: (model, position) => {
          const suggestions = [
            {
              label: 'Django Model',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'class ${1:ModelName}(models.Model):\n    ${2:field_name} = models.${3:CharField}(${4:max_length=100})\n    \n    def __str__(self):\n        return self.${2:field_name}\n    \n    class Meta:\n        verbose_name = "${1:ModelName}"\n        verbose_name_plural = "${1:ModelName}s"',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Django Model class'
            },
            {
              label: 'Django View',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'class ${1:ViewName}(${2:View}):\n    def get(self, request, *args, **kwargs):\n        ${3:pass}\n    \n    def post(self, request, *args, **kwargs):\n        ${4:pass}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Django Class-based View'
            },
            {
              label: 'Django Function View',
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: 'def ${1:view_name}(request):\n    ${2:pass}\n    return render(request, \'${3:template.html}\', {${4:context}})',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Django Function-based View'
            }
          ];

          return { suggestions };
        }
      });
    }

    // Configure JavaScript/TypeScript completions
    if (language === 'javascript' || language === 'typescript') {
      monaco.languages.registerCompletionItemProvider(language, {
        provideCompletionItems: (model, position) => {
          const suggestions = [
            {
              label: 'console.log',
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: 'console.log(${1:message});',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Log to console'
            },
            {
              label: 'React Component',
              kind: monaco.languages.CompletionItemKind.Class,
              insertText: 'const ${1:ComponentName}: React.FC = () => {\n  return (\n    <div>\n      ${2:content}\n    </div>\n  );\n};\n\nexport default ${1:ComponentName};',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'React Functional Component'
            },
            {
              label: 'useState',
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: 'const [${1:state}, set${1/(.*)/${1:/capitalize}/}] = useState(${2:initialValue});',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'React useState hook'
            },
            {
              label: 'useEffect',
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: 'useEffect(() => {\n  ${1:effect}\n}, [${2:dependencies}]);',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'React useEffect hook'
            }
          ];

          return { suggestions };
        }
      });
    }
  };

  const handleEditorChange: OnChange = (value) => {
    onChange(value || '');
  };

  return (
    <div className="h-full w-full">
      <Editor
        height="100%"
        language={language}
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        theme="vs-dark"
        options={{
          selectOnLineNumbers: true,
          matchBrackets: 'always',
          autoClosingBrackets: 'always',
          autoClosingQuotes: 'always',
          autoIndent: 'full',
          formatOnPaste: true,
          formatOnType: true,
        }}
      />
    </div>
  );
};

export default CodeEditor;