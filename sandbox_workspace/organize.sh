#!/bin/bash
#============================================================
# 文件整理脚本 - organize.sh
# 功能：将 test_organize01 目录下的文件按类型归类到子目录中
#============================================================

TARGET_DIR="test_organize01"

echo "=========================================="
echo "  📂 开始整理目录: $TARGET_DIR"
echo "=========================================="

# 定义文件类型与分类目录的映射关系
declare -A TYPE_MAP
TYPE_MAP=(
    ["py"]="scripts"
    ["sh"]="scripts"
    ["json"]="data"
    ["csv"]="data"
    ["md"]="documents"
    ["txt"]="documents"
    ["pdf"]="documents"
    ["pptx"]="documents"
    ["jpg"]="images"
    ["png"]="images"
    ["gif"]="images"
    ["mp3"]="audio"
    ["wav"]="audio"
    ["mp4"]="video"
)

# 统计计数器
moved_count=0
skipped_count=0

# 遍历目标目录下的所有普通文件（不包含子目录中的文件）
for filepath in "$TARGET_DIR"/*; do
    # 跳过非文件（如目录）
    [ -f "$filepath" ] || continue

    filename=$(basename "$filepath")

    # 跳过隐藏文件（以 . 开头的文件）
    if [[ "$filename" == .* ]]; then
        echo "  ⏭️  跳过隐藏文件: $filename"
        ((skipped_count++))
        continue
    fi

    # 获取文件扩展名（转小写）
    ext="${filename##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    # 如果没有扩展名，放入 others 目录
    if [ "$ext" = "$filename" ]; then
        category="others"
    else
        # 查找映射，未匹配则用扩展名作为目录名
        category="${TYPE_MAP[$ext]:-$ext}"
    fi

    # 创建分类目录（如果不存在）
    dest_dir="$TARGET_DIR/$category"
    mkdir -p "$dest_dir"

    # 移动文件
    mv "$filepath" "$dest_dir/$filename"
    echo "  ✅ $filename  →  $category/"
    ((moved_count++))
done

echo ""
echo "=========================================="
echo "  📊 整理完成！"
echo "  ✅ 已移动: ${moved_count} 个文件"
echo "  ⏭️  已跳过: ${skipped_count} 个文件"
echo "=========================================="
echo ""
echo "📁 整理后的目录结构："
find "$TARGET_DIR" -type d | sort | while read dir; do
    count=$(find "$dir" -maxdepth 1 -type f | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "  $dir/ ($count 个文件)"
    fi
done
