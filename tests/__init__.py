# 让 `python -m unittest discover -s tests -t .` 能显式地从仓库根解析 `import main`，
# 而不是依赖 "当前工作目录恰好在 sys.path 上" 这种隐式行为。
