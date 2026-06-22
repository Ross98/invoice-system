<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="text-h5">
        关于发票管理系统
      </v-card-title>
      <v-card-subtitle>本地部署的企业发票管理解决方案</v-card-subtitle>
    </v-card>

    <v-row>
      <v-col
        cols="12"
        md="6"
      >
        <v-card>
          <v-card-title>系统信息</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <v-list-item-title>版本</v-list-item-title>
                <v-list-item-subtitle>v2.0.0</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>构建日期</v-list-item-title>
                <v-list-item-subtitle>2026-05-22</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>技术栈</v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip
                    size="small"
                    class="mr-1 mb-1"
                  >
                    Python FastAPI
                  </v-chip>
                  <v-chip
                    size="small"
                    class="mr-1 mb-1"
                  >
                    Vue.js 3
                  </v-chip>
                  <v-chip
                    size="small"
                    class="mr-1 mb-1"
                  >
                    Vuetify 3
                  </v-chip>
                  <v-chip
                    size="small"
                    class="mr-1 mb-1"
                  >
                    SQLite
                  </v-chip>
                  <v-chip
                    size="small"
                    class="mr-1 mb-1"
                  >
                    Tesseract OCR
                  </v-chip>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>许可证</v-list-item-title>
                <v-list-item-subtitle>MIT License</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col
        cols="12"
        md="6"
      >
        <v-card>
          <v-card-title>主要功能</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <template #prepend>
                  <v-icon color="green">
                    mdi-check-circle
                  </v-icon>
                </template>
                <v-list-item-title>发票信息管理</v-list-item-title>
                <v-list-item-subtitle>录入、查询、编辑、删除发票</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template #prepend>
                  <v-icon color="green">
                    mdi-check-circle
                  </v-icon>
                </template>
                <v-list-item-title>消费明细管理</v-list-item-title>
                <v-list-item-subtitle>记录每笔消费的详细信息</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template #prepend>
                  <v-icon color="green">
                    mdi-check-circle
                  </v-icon>
                </template>
                <v-list-item-title>发票原文件管理</v-list-item-title>
                <v-list-item-subtitle>PDF/图片上传、预览、下载</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template #prepend>
                  <v-icon color="green">
                    mdi-check-circle
                  </v-icon>
                </template>
                <v-list-item-title>OCR 自动识别</v-list-item-title>
                <v-list-item-subtitle>本地 Tesseract + 云端 API 备用</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template #prepend>
                  <v-icon color="green">
                    mdi-check-circle
                  </v-icon>
                </template>
                <v-list-item-title>搜索与统计</v-list-item-title>
                <v-list-item-subtitle>全文搜索、高级筛选、报表统计</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>系统架构</v-card-title>
          <v-card-text>
            <v-card
              variant="outlined"
              class="pa-4"
            >
              <div class="text-center">
                <div class="text-h6 mb-2">
                  前端 (Vue.js 3 + Vuetify 3)
                </div>
                <v-icon>mdi-arrow-down</v-icon>
                <div class="text-h6 my-2">
                  后端 API (Python FastAPI)
                </div>
                <v-icon>mdi-arrow-down</v-icon>
                <div class="text-h6 my-2">
                  数据层 (SQLite + 本地文件系统)
                </div>
              </div>
            </v-card>
            <div class="mt-4">
              <p><strong>特点：</strong></p>
              <ul>
                <li><strong>完全本地部署</strong>：数据存储在本地，无需网络连接</li>
                <li><strong>隐私安全</strong>：发票信息不上传云端，保护企业隐私</li>
                <li><strong>零配置</strong>：SQLite 数据库，无需安装数据库服务</li>
                <li><strong>混合存储</strong>：小文件存数据库，大文件存本地文件夹</li>
                <li><strong>OCR 灵活配置</strong>：本地 Tesseract + 可选云端 API</li>
              </ul>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>使用说明</v-card-title>
          <v-card-text>
            <v-stepper
              v-model="step"
              vertical
            >
              <v-stepper-step
                :complete="step > 1"
                step="1"
              >
                初始化设置
                <small>配置分类、单位等基础信息</small>
              </v-stepper-step>
              <v-stepper-content step="1">
                <v-card
                  variant="outlined"
                  class="mb-4"
                >
                  <v-card-text>
                    <p>1. 在"分类管理"中添加消费分类（如：办公用品、差旅费、招待费等）</p>
                    <p>2. 在"单位管理"中添加常用对方单位信息</p>
                    <p>3. 在"系统设置"中配置 OCR 和文件存储选项</p>
                  </v-card-text>
                </v-card>
                <v-btn
                  color="primary"
                  @click="step = 2"
                >
                  下一步
                </v-btn>
              </v-stepper-content>

              <v-stepper-step
                :complete="step > 2"
                step="2"
              >
                录入发票
                <small>手动录入或 OCR 自动识别</small>
              </v-stepper-step>
              <v-stepper-content step="2">
                <v-card
                  variant="outlined"
                  class="mb-4"
                >
                  <v-card-text>
                    <p><strong>方法一：手动录入</strong></p>
                    <p>1. 点击"新建发票"进入表单页面</p>
                    <p>2. 填写发票号码、代码、日期、金额等基本信息</p>
                    <p>3. 添加消费明细行（可选）</p>
                    <p>4. 保存发票</p>
                    
                    <p class="mt-4">
                      <strong>方法二：OCR 自动识别</strong>
                    </p>
                    <p>1. 在"上传发票"页面选择发票文件（PDF/图片）</p>
                    <p>2. 系统自动进行 OCR 识别</p>
                    <p>3. 检查识别结果，确认或修改信息</p>
                    <p>4. 创建发票</p>
                  </v-card-text>
                </v-card>
                <v-btn
                  variant="text"
                  @click="step = 1"
                >
                  上一步
                </v-btn>
                <v-btn
                  color="primary"
                  @click="step = 3"
                >
                  下一步
                </v-btn>
              </v-stepper-content>

              <v-stepper-step
                :complete="step > 3"
                step="3"
              >
                管理与查询
                <small>查看、搜索、统计发票信息</small>
              </v-stepper-step>
              <v-stepper-content step="3">
                <v-card
                  variant="outlined"
                  class="mb-4"
                >
                  <v-card-text>
                    <p>1. 在"发票管理"页面查看所有发票列表</p>
                    <p>2. 使用搜索框和筛选条件快速定位发票</p>
                    <p>3. 点击发票行查看详细信息</p>
                    <p>4. 在详情页上传、下载、删除发票原文件</p>
                    <p>5. 使用统计功能分析消费情况</p>
                  </v-card-text>
                </v-card>
                <v-btn
                  variant="text"
                  @click="step = 2"
                >
                  上一步
                </v-btn>
                <v-btn
                  color="primary"
                  @click="step = 4"
                >
                  下一步
                </v-btn>
              </v-stepper-content>

              <v-stepper-step step="4">
                数据维护
                <small>备份、恢复、系统维护</small>
              </v-stepper-step>
              <v-stepper-content step="4">
                <v-card
                  variant="outlined"
                  class="mb-4"
                >
                  <v-card-text>
                    <p><strong>定期备份：</strong>在"系统设置"中定期备份数据库</p>
                    <p><strong>文件管理：</strong>系统会自动清理未关联的临时文件</p>
                    <p><strong>系统更新：</strong>关注新版本，获取功能改进和 bug 修复</p>
                    <p><strong>问题反馈：</strong>遇到问题请记录错误信息并联系开发者</p>
                  </v-card-text>
                </v-card>
                <v-btn
                  variant="text"
                  @click="step = 3"
                >
                  上一步
                </v-btn>
              </v-stepper-content>
            </v-stepper>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>技术支持</v-card-title>
          <v-card-text>
            <v-alert
              type="info"
              class="mb-4"
            >
              本系统为开源项目，如需技术支持或功能定制，请联系开发者
            </v-alert>
            <v-list>
              <v-list-item>
                <v-list-item-title>GitHub 仓库</v-list-item-title>
                <v-list-item-subtitle>https://github.com/Ross98/invoice-system</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>问题反馈</v-list-item-title>
                <v-list-item-subtitle>aka_chuanfengdada@qq.com</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>文档</v-list-item-title>
                <v-list-item-subtitle>https://github.com/Ross98/invoice-system/blob/V2.0/docs/UX-ARCHITECTURE.md</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref } from "vue";

const step = ref(1);
</script>