import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  List,
  ListItem,
  Code,
  Grid,
  GridItem,
} from '@chakra-ui/react'
import type { RegistryEntry } from './data';

interface RegistryProps {
    registry: Record<string, RegistryEntry>;
}

function Registry(props: RegistryProps) {
    const { registry } = props;
    return (
        <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }} gap={6}>
            {Object.entries(registry).map(([key, entry]) => (
            <GridItem key={key}>
                <Box
                borderWidth="1px"
                borderRadius="md"
                p={4}
                bg="white"
                shadow="sm"
                h="100%"
                >
                <VStack align="start" gap={3}>
                    <Heading as="h3" size="md" color="blue.600">
                    {key}
                    </Heading>

                    <Box>
                    <Text fontWeight="semibold">Interface:</Text>
                    <VStack align="start" gap={1} mt={1}>
                        <HStack>
                        <Text fontSize="sm">Function:</Text>
                        <Code fontSize="sm">{entry.interface.func}</Code>
                        </HStack>
                        <HStack>
                        <Text fontSize="sm">ID:</Text>
                        <Code fontSize="sm">{entry.interface.id}</Code>
                        </HStack>
                    </VStack>
                    </Box>

                    <Box>
                    <Text fontWeight="semibold">Functions:</Text>
                    <VStack align="start" gap={1} mt={1}>
                        {Object.entries(entry.funcs).map(([funcName, funcImpl]) => (
                        <HStack key={funcName}>
                            <Text fontSize="sm">{funcName}:</Text>
                            <Code fontSize="sm">{funcImpl.id}</Code>
                        </HStack>
                        ))}
                        {Object.keys(entry.funcs).length === 0 && (
                        <Text fontSize="sm" color="gray.500">No functions</Text>
                        )}
                    </VStack>
                    </Box>

                    <Box>
                    <Text fontWeight="semibold" mb={2}>Rules:</Text>
                    <List.Root>
                        {entry.rules.map((rule, index) => (
                        <ListItem key={index}>
                            <VStack align="start" gap={1}>
                            <HStack>
                                <Text fontSize="xs">Selector:</Text>
                                <Code fontSize="xs">{rule.selector}</Code>
                            </HStack>
                            <HStack>
                                <Text fontSize="xs">Impl:</Text>
                                <Code fontSize="xs">{rule.impl}</Code>
                            </HStack>
                            </VStack>
                        </ListItem>
                        ))}
                        {entry.rules.length === 0 && (
                        <Text fontSize="sm" color="gray.500">No rules</Text>
                        )}
                    </List.Root>
                    </Box>
                </VStack>
                </Box>
            </GridItem>
            ))}
        </Grid>
    );
}

export default Registry
