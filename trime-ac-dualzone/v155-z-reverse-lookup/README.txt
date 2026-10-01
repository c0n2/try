Trime AC v1.5.5 — Z 拼音反查数据补丁
=====================================

目的
----
在正式方案 ac_raincandy_wubi86 中启用官方 Rime 五笔风格的 Z 拼音反查：

  五笔中文模式 -> 输入 z + 拼音
  例如：zni
  -> 出现“你、尼、泥……”等拼音候选
  -> 候选若存在于 AC 五笔码表中，候选注释显示对应五笔编码
  -> 选择候选后正常上屏汉字

安装位置
--------
把本 ZIP 中以下文件复制到 Trime AC 专用外部目录 AC-Trime 的根目录：

  ac_raincandy_wubi86.custom.yaml
  pinyin_simp.dict.yaml
  pinyin_simp.schema.yaml

也就是与现有 ac_raincandy_wubi86.schema.yaml / dict.yaml 同一级。

重要：不要删除、替换或覆盖现有 ac_raincandy_wubi86.schema.yaml。
v1.5.5 使用 .custom.yaml overlay，只给正式 AC schema 增加 Z 反查链。

复制完成后
----------
1. 在 Trime 中执行“同步用户数据”（让 AC-Trime 外部目录导入内部运行目录）。
2. 执行“重新部署 / 部署”使 schema 与 pinyin_simp 词典重新编译。
3. 保持当前方案为 ac_raincandy_wubi86。
4. 测试：输入 zni。

验收
----
- zni 能出现 ni 的中文候选。
- 候选中属于 AC 五笔码表的字，应在注释处显示五笔编码。
- 选择“你”等候选可正常上屏。
- 退格 / Esc 可正常退出反查。
- 普通五笔输入、Ctrl+P 添词不受影响。

来源
----
pinyin_simp 来自官方 rime/rime-pinyin-simp，并固定到 UPSTREAM.txt 所列 commit。
上游 LICENSE 随正式 ZIP 一并提供为 PINYIN_SIMP_LICENSE。
