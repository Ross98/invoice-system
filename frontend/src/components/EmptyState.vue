<template>
  <div class="empty-state">
    <v-icon :size="iconSize" :color="iconColor">{{ icon }}</v-icon>
    <div class="empty-state__title">{{ title }}</div>
    <div v-if="subtitle" class="empty-state__subtitle">{{ subtitle }}</div>
    <v-btn
      v-if="actionText"
      :color="actionColor"
      variant="outlined"
      class="mt-4"
      :prepend-icon="actionIcon"
      @click="$emit('action')"
    >
      {{ actionText }}
    </v-btn>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: 'mdi-inbox-outline' },
  iconSize: { type: [String, Number], default: 64 },
  iconColor: { type: String, default: 'grey-lighten-1' },
  title: { type: String, default: '暂无数据' },
  subtitle: { type: String, default: '' },
  actionText: { type: String, default: '' },
  actionIcon: { type: String, default: 'mdi-plus' },
  actionColor: { type: String, default: 'primary' }
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 1rem;
  text-align: center;
  gap: 0.5rem;
}
.empty-state__title {
  font-size: 1.125rem;
  font-weight: 500;
  color: #757575;
  margin-top: 0.5rem;
}
.empty-state__subtitle {
  font-size: 0.875rem;
  color: #9e9e9e;
  max-width: 400px;
}
</style>
