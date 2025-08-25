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
import type { ChoiceFunction, ChoiceFuncImplementation } from './data';
import { findImplementationName } from './utils';

interface RegistryProps {
    registry: Record<string, ChoiceFunction>;
    highlightedEntryId?: string | null;
    onClearHighlight?: () => void;
}

function ChoiceFuncImplementationDisplay({ impl, name }: { impl: ChoiceFuncImplementation; name?: string }) {
    return (
        <Box borderWidth="1px" borderRadius="sm" p={2} bg="gray.50">
            <VStack align="start" gap={1}>
                {name && (
                    <HStack>
                        <Text fontSize="sm" fontWeight="medium">Name:</Text>
                        <Code fontSize="sm">{name}</Code>
                    </HStack>
                )}
                <HStack>
                    <Text fontSize="sm">Function:</Text>
                    <Code fontSize="sm">{impl.func}</Code>
                </HStack>
                {Object.keys(impl.defaults).length > 0 && (
                    <Box>
                        <Text fontSize="sm" fontWeight="medium">Defaults:</Text>
                        <VStack align="start" gap={1} ml={2}>
                            {Object.entries(impl.defaults).map(([key, value]) => (
                                <HStack key={key}>
                                    <Text fontSize="xs">{key}:</Text>
                                    <Code fontSize="xs">{value}</Code>
                                </HStack>
                            ))}
                        </VStack>
                    </Box>
                )}
            </VStack>
        </Box>
    );
}

function Registry(props: RegistryProps) {
    const { registry, highlightedEntryId, onClearHighlight } = props;
    
    return (
        <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }} gap={6}>
            {Object.entries(registry).map(([key, entry]) => {
                const isHighlighted = highlightedEntryId === entry.id;
                return (
                <GridItem key={key}>
                    <Box
                    borderWidth={isHighlighted ? "3px" : "1px"}
                    borderColor={isHighlighted ? "blue.500" : "gray.200"}
                    borderRadius="md"
                    p={4}
                    bg={isHighlighted ? "blue.50" : "white"}
                    shadow={isHighlighted ? "lg" : "sm"}
                    h="100%"
                    position="relative"
                    >
                    {isHighlighted && (
                        <Box
                        position="absolute"
                        top={2}
                        right={2}
                        bg="blue.500"
                        color="white"
                        px={2}
                        py={1}
                        borderRadius="sm"
                        fontSize="xs"
                        fontWeight="bold"
                        cursor="pointer"
                        onClick={onClearHighlight}
                        _hover={{ bg: "blue.600" }}
                        >
                        ✕
                        </Box>
                    )}
                <VStack align="start" gap={3}>
                    <Heading as="h3" size="md" color="blue.600">
                    {entry.interface.func}
                    </Heading>

                    <Box>
                    <Text fontWeight="semibold" mb={2}>Interface:</Text>
                    <ChoiceFuncImplementationDisplay impl={entry.interface} />
                    </Box>

                    <Box>
                    <Text fontWeight="semibold" mb={2}>Functions:</Text>
                    <VStack align="start" gap={2}>
                        {Object.entries(entry.funcs).map(([funcName, funcImpl]) => (
                            <ChoiceFuncImplementationDisplay 
                                key={funcName} 
                                impl={funcImpl} 
                                name={funcName} 
                            />
                        ))}
                        {Object.keys(entry.funcs).length === 0 && (
                        <Text fontSize="sm" color="gray.500">No additional implementations defined</Text>
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
                                <Code fontSize="xs">{findImplementationName(rule.impl, entry)}</Code>
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
                );
            })}
        </Grid>
    );
}

export default Registry
