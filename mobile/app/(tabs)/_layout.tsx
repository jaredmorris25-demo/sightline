import { Tabs } from 'expo-router'

export default function TabLayout() {
  return (
    <Tabs>
      <Tabs.Screen name="index" options={{ title: 'Map' }} />
      <Tabs.Screen name="species" options={{ title: 'Species' }} />
      <Tabs.Screen name="submit" options={{ title: 'Submit' }} />
    </Tabs>
  )
}
