<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-check-circle</v-icon>
      报销报表
    </v-card-title>
    <v-card-text>
      <v-alert
        type="info"
        variant="tonal"
        text="报销追踪报表功能将在 Phase 3 中实现。目前请使用发票汇总页面查看和导出数据。"
      />
      <v-btn
        color="primary"
        variant="tonal"
        class="mt-4"
        to="/reports/invoice"
      >
        <v-icon start>mdi-file-table</v-icon>
        前往发票汇总
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup>
// Phase 3: Full reimbursement report with charts and filters
</script>
