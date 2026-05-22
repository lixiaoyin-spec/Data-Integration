<?xml version="1.0" encoding="GB2312"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" encoding="GB2312" indent="yes"/>

    <xsl:template match="/Choices">
        <choices>
            <xsl:for-each select="choice">
                <choice>
                    <sid><xsl:value-of select="Sno"/></sid>
                    <cid><xsl:value-of select="Cno"/></cid>
                    <score><xsl:value-of select="Grd"/></score>
                </choice>
            </xsl:for-each>
        </choices>
    </xsl:template>
</xsl:stylesheet>