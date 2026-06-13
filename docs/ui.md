# Desktop UI / 桌面调试界面

Launch the simple desktop panel:

启动简单桌面面板：

```powershell
python -m stellaris_advisor.ui
```

If the package is installed in editable mode, the script entrypoint is also available:

如果已经以 editable 模式安装，也可以使用脚本入口：

```powershell
stellaris-advisor-ui
```

The panel can:

- scan the default Stellaris save folder;
- open a specific `.sav` file;
- choose language, visibility mode, detail level, and strategic focus;
- use optional official localization data;
- use optional local RAG knowledge records;
- generate either a parsed report or a copy/paste LLM prompt;
- copy or save the output.

这个面板可以：

- 扫描默认群星存档目录；
- 打开指定 `.sav` 存档；
- 选择语言、可见度模式、详情等级和战略焦点；
- 使用可选官方本地化数据；
- 使用可选本地 RAG 知识库；
- 生成解析报告或可复制给大模型的 prompt；
- 复制或保存输出。
